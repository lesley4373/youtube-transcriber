from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import yt_dlp
import base64
from urllib.parse import parse_qs

class handler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        
        response = {
            "message": "YouTube Transcriber API",
            "status": "healthy",
            "version": "2.0.0-ai-updated",
            "features": ["yt-dlp", "openai-whisper", "translation"]
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            
            # 检查Content-Type以确定处理方式
            content_type = self.headers.get('Content-Type', '')
            
            if content_type.startswith('multipart/form-data'):
                # 处理文件上传
                boundary = content_type.split('boundary=')[1]
                data, audio_file = self.parse_multipart(body, boundary)
            else:
                # 处理JSON数据
                data = json.loads(body.decode())
                audio_file = None
            
            url = data.get('url', '')
            api_key = data.get('api_key', os.environ.get('OPENAI_API_KEY', ''))
            
            if not url and not audio_file:
                self.send_error_response(400, "URL or audio file is required")
                return
            
            # 获取标题
            if url:
                title = self.get_video_title(url)
            else:
                title = "Uploaded Audio File"
            
            if not api_key:
                # 返回提示需要API密钥的演示数据
                response = {
                    "title": f"[需要API密钥] {title}",
                    "segments": [
                        {
                            "start": 0.0,
                            "end": 5.0,
                            "text": "Please provide OpenAI API key for real transcription.",
                            "translation": "请在Vercel设置中添加OPENAI_API_KEY环境变量，或在输入框中提供API密钥。"
                        },
                        {
                            "start": 5.0,
                            "end": 10.0,
                            "text": "You can get your API key from platform.openai.com",
                            "translation": "您可以从platform.openai.com获取API密钥。"
                        }
                    ]
                }
                self.send_success_response(response)
                return
            
            # 尝试进行真实的转写
            try:
                # 只有有API密钥时才导入这些包
                from openai import OpenAI
                from deep_translator import GoogleTranslator
                
                # 获取音频文件
                if audio_file:
                    # 使用上传的音频文件
                    final_audio_file = audio_file
                else:
                    # 从YouTube下载音频
                    final_audio_file = self.download_audio(url)
                
                # 转写
                client = OpenAI(api_key=api_key)
                segments = self.transcribe_audio(final_audio_file, client)
                
                # 翻译
                translator = GoogleTranslator(source='en', target='zh-cn')
                translated_segments = self.translate_segments(segments, translator)
                
                # 清理文件
                try:
                    os.remove(final_audio_file)
                except:
                    pass
                
                response = {
                    "title": title,
                    "segments": translated_segments
                }
                self.send_success_response(response)
                
            except Exception as e:
                # 如果AI处理失败，返回错误信息
                error_response = {
                    "title": f"[处理失败] {title}",
                    "segments": [
                        {
                            "start": 0.0,
                            "end": 5.0,
                            "text": f"AI processing failed: {str(e)}",
                            "translation": f"AI处理失败: {str(e)}"
                        }
                    ]
                }
                self.send_success_response(error_response)
                
        except Exception as e:
            self.send_error_response(500, f"Request error: {str(e)}")
    
    def parse_multipart(self, body, boundary):
        """Parse multipart/form-data"""
        try:
            boundary_bytes = boundary.encode()
            parts = body.split(b'--' + boundary_bytes)
            
            data = {}
            audio_file = None
            
            for part in parts:
                if b'Content-Disposition' not in part:
                    continue
                    
                # 提取头部和内容
                if b'\r\n\r\n' in part:
                    header, content = part.split(b'\r\n\r\n', 1)
                    header_str = header.decode()
                    
                    # 提取字段名
                    if 'name="' in header_str:
                        field_name = header_str.split('name="')[1].split('"')[0]
                        
                        if field_name == 'audio':
                            # 保存音频文件
                            temp_dir = '/tmp'
                            import uuid
                            unique_id = str(uuid.uuid4())[:8]
                            audio_filename = os.path.join(temp_dir, f'uploaded_{unique_id}.mp3')
                            
                            with open(audio_filename, 'wb') as f:
                                f.write(content.rstrip(b'\r\n'))
                            
                            audio_file = audio_filename
                        else:
                            # 其他字段
                            data[field_name] = content.decode().rstrip('\r\n')
            
            return data, audio_file
            
        except Exception as e:
            print(f"Multipart parsing error: {e}")
            return {}, None
    
    def download_audio(self, url):
        """Download audio from YouTube - Optimized for Vercel"""
        try:
            # 使用/tmp目录，Vercel中唯一可写的目录
            temp_dir = '/tmp'
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            output_path = os.path.join(temp_dir, f'audio_{unique_id}')
            
            # 优化配置，增强反检测能力
            ydl_opts = {
                'format': 'bestaudio[ext=m4a][filesize<25M]/bestaudio[filesize<25M]/best[filesize<25M]',
                'outtmpl': output_path + '.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'prefer_ffmpeg': False,  # 不强制使用FFmpeg
                'extract_flat': False,
                # 增强反检测措施
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                },
                'extractor_retries': 5,
                'sleep_interval': 2,
                'max_sleep_interval': 10,
                'skip_unavailable_fragments': True,
                'ignoreerrors': False,
                # 添加cookies支持（模拟真实用户）
                'cookiefile': None,
                'cookiesfrombrowser': None,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 首先获取视频信息
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("无法获取视频信息")
                
                # 检查视频长度（限制在10分钟内）
                duration = info.get('duration', 0)
                if duration > 600:  # 10分钟
                    raise Exception("视频太长，请使用10分钟以内的视频")
                
                # 下载音频
                ydl.download([url])
            
            # 查找下载的文件
            for file in os.listdir(temp_dir):
                if file.startswith(f'audio_{unique_id}') and (file.endswith('.m4a') or file.endswith('.mp3') or file.endswith('.webm')):
                    file_path = os.path.join(temp_dir, file)
                    # 检查文件大小
                    file_size = os.path.getsize(file_path)
                    if file_size < 25 * 1024 * 1024 and file_size > 0:  # 25MB且不为空
                        return file_path
            
            raise Exception("下载的音频文件未找到或为空")
            
        except Exception as e:
            print(f"Download error: {e}")
            raise Exception(f"音频下载失败: {str(e)}")
    
    def transcribe_audio(self, audio_file, client):
        """Transcribe using OpenAI Whisper"""
        try:
            with open(audio_file, 'rb') as audio:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            segments = []
            if hasattr(response, 'segments') and response.segments:
                for seg in response.segments:
                    segments.append({
                        "start": seg.get('start', 0),
                        "end": seg.get('end', 0),
                        "text": seg.get('text', '').strip()
                    })
            else:
                # Fallback
                text = getattr(response, 'text', str(response))
                segments.append({
                    "start": 0,
                    "end": 30,
                    "text": text
                })
            
            return segments
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return [{
                "start": 0,
                "end": 5,
                "text": f"Transcription failed: {str(e)}"
            }]
    
    def translate_segments(self, segments, translator):
        """Translate to Chinese using deep-translator"""
        translated = []
        for seg in segments:
            try:
                translation = translator.translate(seg['text'])
                translated.append({
                    "start": seg['start'],
                    "end": seg['end'],
                    "text": seg['text'],
                    "translation": translation
                })
            except Exception as e:
                print(f"Translation error: {e}")
                translated.append({
                    "start": seg['start'],
                    "end": seg['end'],
                    "text": seg['text'],
                    "translation": seg['text']  # Fallback
                })
        return translated
    
    def get_video_title(self, url):
        """Get YouTube video title"""
        try:
            ydl_opts = {
                'quiet': True, 
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                },
                'extractor_retries': 5,
                'sleep_interval': 2,
                'skip_unavailable_fragments': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('title', 'Unknown Video')
        except Exception as e:
            print(f"Title extraction error: {e}")
            return "YouTube Video"
    
    def send_success_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        
        error_response = {"error": message, "code": code}
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
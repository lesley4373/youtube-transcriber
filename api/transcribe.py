from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import yt_dlp

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
            data = json.loads(body.decode())
            
            url = data.get('url', '')
            api_key = data.get('api_key', os.environ.get('OPENAI_API_KEY', ''))
            
            if not url:
                self.send_error_response(400, "URL is required")
                return
            
            # 获取视频标题
            title = self.get_video_title(url)
            
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
                from googletrans import Translator
                
                # 下载音频
                audio_file = self.download_audio(url)
                if not audio_file:
                    raise Exception("音频下载失败")
                
                # 转写
                client = OpenAI(api_key=api_key)
                segments = self.transcribe_audio(audio_file, client)
                
                # 翻译
                translator = Translator()
                translated_segments = self.translate_segments(segments, translator)
                
                # 清理文件
                try:
                    os.remove(audio_file)
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
    
    def download_audio(self, url):
        """Download audio from YouTube"""
        try:
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, 'audio')
            
            ydl_opts = {
                'format': 'bestaudio[filesize<25M]/best[filesize<25M]',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'outtmpl': output_path + '.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 查找下载的文件
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    file_path = os.path.join(temp_dir, file)
                    # 检查文件大小
                    if os.path.getsize(file_path) < 25 * 1024 * 1024:  # 25MB
                        return file_path
            
            return None
            
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
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
        """Translate to Chinese"""
        translated = []
        for seg in segments:
            try:
                translation = translator.translate(seg['text'], dest='zh-cn')
                translated.append({
                    "start": seg['start'],
                    "end": seg['end'],
                    "text": seg['text'],
                    "translation": translation.text if hasattr(translation, 'text') else str(translation)
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
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('title', 'Unknown Video')
        except:
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
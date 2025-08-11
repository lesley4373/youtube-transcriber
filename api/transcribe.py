from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import yt_dlp
import base64
from urllib.parse import parse_qs
import re

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
            "features": ["yt-dlp", "openai-whisper", "translation", "base64-upload"],
            "timestamp": str(os.getenv('VERCEL_DEPLOYMENT_ID', 'local')),
            "test": "API is working"
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            
            # 处理JSON数据
            data = json.loads(body.decode())
            
            url = data.get('url', '')
            api_key = data.get('api_key', os.environ.get('OPENAI_API_KEY', ''))
            audio_base64 = data.get('audio_base64', '')
            filename = data.get('filename', 'audio.mp3')
            subtitle_text = data.get('subtitle_text', '')
            
            # 处理base64音频文件
            audio_file = None
            if audio_base64:
                audio_file = self.save_base64_audio(audio_base64, filename)
            
            if not url and not audio_file and not subtitle_text:
                self.send_error_response(400, "URL, audio file, or subtitle text is required")
                return
            
            # 获取标题
            if url:
                title = self.get_video_title(url)
            elif subtitle_text:
                title = "Pasted Subtitles"
            else:
                title = "Uploaded Audio File"
            
            if not api_key:
                # 没有API密钥时的处理
                print("No API key provided")
                
                if audio_file:
                    # 音频文件上传需要API密钥
                    response = {
                        "title": f"[需要API密钥] {title}",
                        "segments": [
                            {
                                "start": 0.0,
                                "end": 5.0,
                                "text": "Audio file transcription requires OpenAI API key.",
                                "translation": "音频文件转录需要OpenAI API密钥。"
                            },
                            {
                                "start": 5.0,
                                "end": 10.0,
                                "text": "You can get your API key from platform.openai.com",
                                "translation": "您可以从 platform.openai.com 获取API密钥。"
                            }
                        ]
                    }
                    self.send_success_response(response)
                    return
                elif subtitle_text:
                    # 字幕文本处理，无需API密钥但无翻译
                    try:
                        segments = self.parse_simple_subtitles(subtitle_text)
                        translated_segments = []
                        for seg in segments:
                            translated_segments.append({
                                "start": seg['start'],
                                "end": seg['end'],
                                "text": seg['text'],
                                "translation": f"[需要API密钥进行翻译] {seg['text'][:30]}..."
                            })
                        
                        response = {
                            "title": f"[仅英文] {title}",
                            "segments": translated_segments
                        }
                        self.send_success_response(response)
                        return
                    except Exception as e:
                        response = {
                            "title": f"[解析失败] {title}",
                            "segments": [
                                {
                                    "start": 0.0,
                                    "end": 5.0,
                                    "text": f"Subtitle parsing failed: {str(e)}",
                                    "translation": f"字幕解析失败: {str(e)}"
                                }
                            ]
                        }
                        self.send_success_response(response)
                        return
                else:
                    # YouTube字幕提取不需要API密钥，但翻译需要
                    try:
                        print("Extracting subtitles without API key...")
                        subtitle_content, video_title = self.extract_subtitles(url)
                        title = video_title
                        segments = self.parse_subtitles(subtitle_content)
                        
                        # 不翻译，只返回英文字幕
                        translated_segments = []
                        for seg in segments:
                            translated_segments.append({
                                "start": seg['start'],
                                "end": seg['end'],
                                "text": seg['text'],
                                "translation": f"[需要API密钥进行中文翻译] {seg['text'][:50]}..."
                            })
                        
                        response = {
                            "title": f"[仅英文字幕] {title}",
                            "segments": translated_segments
                        }
                        self.send_success_response(response)
                        return
                        
                    except Exception as e:
                        # 字幕提取失败，返回演示数据
                        response = {
                            "title": f"[字幕提取失败] {title}",
                            "segments": [
                                {
                                    "start": 0.0,
                                    "end": 5.0,
                                    "text": f"Subtitle extraction failed: {str(e)}",
                                    "translation": f"字幕提取失败: {str(e)}"
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
                
                segments = []
                
                if audio_file:
                    # 使用上传的音频文件进行AI转录
                    final_audio_file = audio_file
                    print(f"Using uploaded audio file: {final_audio_file}")
                    # 检查文件是否存在和大小
                    if os.path.exists(final_audio_file):
                        file_size = os.path.getsize(final_audio_file)
                        print(f"File exists, size: {file_size} bytes")
                        if file_size == 0:
                            raise Exception("上传的文件为空")
                    else:
                        raise Exception(f"上传的文件不存在: {final_audio_file}")
                    
                    # 转写
                    print(f"Starting transcription with OpenAI...")
                    client = OpenAI(api_key=api_key)
                    segments = self.transcribe_audio(final_audio_file, client)
                    print(f"Transcription complete, got {len(segments)} segments")
                    
                elif subtitle_text:
                    # 处理粘贴的字幕文本
                    print(f"Processing pasted subtitle text...")
                    segments = self.parse_simple_subtitles(subtitle_text)
                    print(f"Subtitle text processing complete, got {len(segments)} segments")
                    
                else:
                    # 先测试音频URL提取，不进行转录
                    try:
                        print(f"Testing audio URL extraction...")
                        audio_url, video_title = self.get_audio_url(url)
                        title = video_title
                        
                        # 返回测试结果而不是转录
                        segments = [{
                            "start": 0.0,
                            "end": 5.0,
                            "text": f"✓ 音频URL提取成功！",
                            "translation": f"✓ Audio URL extraction successful!"
                        }, {
                            "start": 5.0,
                            "end": 10.0,
                            "text": f"URL: {audio_url[:100]}...",
                            "translation": f"音频链接: {audio_url[:100]}..."
                        }, {
                            "start": 10.0,
                            "end": 15.0,
                            "text": f"准备就绪，可以进行AI转录",
                            "translation": f"Ready for AI transcription"
                        }]
                        print(f"Audio URL extraction test successful")
                        
                    except Exception as audio_error:
                        print(f"Audio URL method failed: {audio_error}")
                        # 回退到字幕提取方法
                        try:
                            print(f"Falling back to subtitle extraction...")
                            subtitle_content, video_title = self.extract_subtitles(url)
                            title = video_title
                            segments = self.parse_subtitles(subtitle_content)
                            print(f"Subtitle extraction complete, got {len(segments)} segments")
                        except Exception as subtitle_error:
                            print(f"Both methods failed. Audio: {audio_error}, Subtitle: {subtitle_error}")
                            # 返回友好的错误提示
                            raise Exception(f"YouTube访问被限制。请尝试: 1) 使用'Paste Subtitles'功能手动粘贴字幕, 2) 上传音频文件, 或 3) 稍后重试")
                
                # 翻译
                print(f"Starting translation...")
                translator = GoogleTranslator(source='en', target='zh-cn')
                translated_segments = self.translate_segments(segments, translator)
                print(f"Translation complete")
                
                # 清理文件
                if audio_file:  # 只有上传的文件才需要清理
                    try:
                        if os.path.exists(final_audio_file):
                            os.remove(final_audio_file)
                            print(f"Cleaned up file: {final_audio_file}")
                    except Exception as cleanup_error:
                        print(f"Cleanup error: {cleanup_error}")
                
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
    
    def save_base64_audio(self, base64_data, filename):
        """Save base64 encoded audio to a temporary file"""
        try:
            # 移除data URL前缀（如果存在）
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            # 解码base64数据
            audio_data = base64.b64decode(base64_data)
            
            # 获取文件扩展名
            file_ext = '.mp3'
            if '.' in filename:
                file_ext = '.' + filename.split('.')[-1].lower()
            
            # 保存到临时文件
            temp_dir = '/tmp'
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            audio_path = os.path.join(temp_dir, f'audio_{unique_id}{file_ext}')
            
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            print(f"Saved base64 audio to: {audio_path}, size: {len(audio_data)} bytes")
            return audio_path
            
        except Exception as e:
            print(f"Error saving base64 audio: {e}")
            return None
    
    def parse_multipart(self, body, boundary):
        """Parse multipart/form-data"""
        try:
            # 处理boundary格式
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]
            
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
                    header_str = header.decode('utf-8', errors='ignore')
                    
                    # 提取字段名
                    if 'name="' in header_str:
                        field_name = header_str.split('name="')[1].split('"')[0]
                        
                        if field_name == 'audio':
                            # 获取文件扩展名
                            file_ext = '.mp3'
                            if 'filename="' in header_str:
                                filename = header_str.split('filename="')[1].split('"')[0]
                                if '.' in filename:
                                    file_ext = '.' + filename.split('.')[-1]
                            
                            # 保存音频文件
                            temp_dir = '/tmp'
                            import uuid
                            unique_id = str(uuid.uuid4())[:8]
                            audio_filename = os.path.join(temp_dir, f'uploaded_{unique_id}{file_ext}')
                            
                            # 去除尾部的boundary标记
                            content = content.rstrip(b'\r\n--')
                            
                            with open(audio_filename, 'wb') as f:
                                f.write(content)
                            
                            audio_file = audio_filename
                            print(f"Saved uploaded file: {audio_filename}, size: {len(content)} bytes")
                        else:
                            # 其他字段
                            content_str = content.decode('utf-8', errors='ignore').rstrip('\r\n--')
                            data[field_name] = content_str
                            print(f"Parsed field {field_name}: {content_str[:50]}...")
            
            return data, audio_file
            
        except Exception as e:
            print(f"Multipart parsing error: {e}")
            import traceback
            traceback.print_exc()
            return {}, None
    
    def extract_subtitles(self, url):
        """Extract subtitles from YouTube - No download needed"""
        try:
            print(f"Extracting subtitles from: {url}")
            
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,  # 包括自动生成的字幕
                'subtitleslangs': ['en', 'en-US', 'en-GB'],  # 优先英文字幕
                'skip_download': True,  # 不下载视频
                'quiet': True,
                'no_warnings': True,
                # 反检测措施
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                },
                'extractor_retries': 3,
                'sleep_interval': 1,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息，包括字幕
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("无法获取视频信息")
                
                # 获取字幕数据
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})
                
                print(f"Available subtitles: {list(subtitles.keys())}")
                print(f"Available auto captions: {list(automatic_captions.keys())}")
                
                # 优先使用手动字幕，然后是自动字幕
                subtitle_data = None
                subtitle_lang = None
                
                # 检查手动字幕
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in subtitles:
                        subtitle_data = subtitles[lang]
                        subtitle_lang = lang
                        print(f"Found manual subtitles in {lang}")
                        break
                
                # 如果没有手动字幕，使用自动字幕
                if not subtitle_data:
                    for lang in ['en', 'en-US', 'en-GB']:
                        if lang in automatic_captions:
                            subtitle_data = automatic_captions[lang]
                            subtitle_lang = lang
                            print(f"Found auto captions in {lang}")
                            break
                
                if not subtitle_data:
                    raise Exception("没有找到英文字幕")
                
                # 获取字幕内容
                subtitle_url = None
                for format_data in subtitle_data:
                    if format_data.get('ext') in ['vtt', 'srv3', 'ttml']:
                        subtitle_url = format_data.get('url')
                        break
                
                if not subtitle_url:
                    raise Exception("无法获取字幕下载链接")
                
                print(f"Downloading subtitles from: {subtitle_url}")
                
                # 下载字幕内容
                import urllib.request
                with urllib.request.urlopen(subtitle_url) as response:
                    subtitle_content = response.read().decode('utf-8')
                
                return subtitle_content, info.get('title', 'Unknown Video')
                
        except Exception as e:
            print(f"Subtitle extraction error: {e}")
            raise Exception(f"字幕提取失败: {str(e)}")
    
    def parse_subtitles(self, subtitle_content):
        """Parse VTT/SRT subtitle format to segments"""
        try:
            segments = []
            
            # VTT格式解析
            if 'WEBVTT' in subtitle_content:
                print("Parsing VTT format")
                lines = subtitle_content.split('\n')
                current_segment = {}
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
                        continue
                    
                    # 时间戳行 (格式: 00:00:01.000 --> 00:00:05.000)
                    if '-->' in line:
                        time_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})', line)
                        if time_match:
                            start_time = self.time_to_seconds(time_match.group(1))
                            end_time = self.time_to_seconds(time_match.group(2))
                            current_segment = {
                                'start': start_time,
                                'end': end_time,
                                'text': ''
                            }
                    
                    # 文本行
                    elif line and 'start' in current_segment:
                        # 去除HTML标签
                        clean_text = re.sub(r'<[^>]+>', '', line)
                        if clean_text.strip():
                            if current_segment['text']:
                                current_segment['text'] += ' ' + clean_text.strip()
                            else:
                                current_segment['text'] = clean_text.strip()
                    
                    # 空行表示段落结束
                    elif not line and current_segment.get('text'):
                        segments.append(current_segment)
                        current_segment = {}
                
                # 添加最后一个segment
                if current_segment.get('text'):
                    segments.append(current_segment)
            
            # 如果解析失败，尝试简单的文本提取
            if not segments:
                print("Fallback to simple text extraction")
                # 提取所有文本，创建一个简单的segment
                clean_text = re.sub(r'<[^>]+>', '', subtitle_content)
                clean_text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}', '', clean_text)
                clean_text = '\n'.join([line.strip() for line in clean_text.split('\n') if line.strip() and not line.strip().startswith('WEBVTT')])
                
                if clean_text:
                    segments = [{
                        'start': 0.0,
                        'end': 30.0,
                        'text': clean_text[:500] + ('...' if len(clean_text) > 500 else '')
                    }]
            
            print(f"Parsed {len(segments)} subtitle segments")
            return segments
            
        except Exception as e:
            print(f"Subtitle parsing error: {e}")
            return [{
                'start': 0.0,
                'end': 10.0,
                'text': '字幕解析失败，请尝试其他视频'
            }]
    
    def time_to_seconds(self, time_str):
        """Convert time string (HH:MM:SS.mmm) to seconds"""
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        except:
            return 0.0
    
    def parse_simple_subtitles(self, subtitle_text):
        """Parse simple subtitle text format"""
        try:
            segments = []
            lines = subtitle_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 尝试解析时间戳格式: "0:00 Text" 或 "0:00:00 Text"
                time_match = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$', line)
                if time_match:
                    time_str = time_match.group(1)
                    text = time_match.group(2)
                    
                    # 转换时间为秒
                    time_parts = time_str.split(':')
                    if len(time_parts) == 2:  # MM:SS
                        start_time = int(time_parts[0]) * 60 + int(time_parts[1])
                    else:  # HH:MM:SS
                        start_time = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
                    
                    segments.append({
                        'start': start_time,
                        'end': start_time + 5,  # 默认5秒段落
                        'text': text
                    })
                else:
                    # 如果没有时间戳，创建连续的段落
                    start_time = len(segments) * 5
                    segments.append({
                        'start': start_time,
                        'end': start_time + 5,
                        'text': line
                    })
            
            if not segments:
                # 如果没有解析出任何段落，将整个文本作为一个段落
                segments.append({
                    'start': 0.0,
                    'end': 30.0,
                    'text': subtitle_text[:500] + ('...' if len(subtitle_text) > 500 else '')
                })
            
            print(f"Parsed {len(segments)} simple subtitle segments")
            return segments
            
        except Exception as e:
            print(f"Simple subtitle parsing error: {e}")
            return [{
                'start': 0.0,
                'end': 10.0,
                'text': subtitle_text[:200] + ('...' if len(subtitle_text) > 200 else '')
            }]
    
    def get_audio_url(self, url):
        """Extract direct audio URL from YouTube without downloading"""
        try:
            print(f"Extracting audio URL from: {url}")
            
            # 尝试多种格式和策略
            format_attempts = [
                'worstaudio',  # 最低质量，较少被检测
                'bestaudio[acodec=mp4a]',  # MP4音频编码
                'bestaudio[ext=m4a]',  # M4A格式
                'bestaudio'  # 最佳音频
            ]
            
            for format_str in format_attempts:
                try:
                    print(f"Trying format: {format_str}")
                    
                    ydl_opts = {
                        'format': format_str,
                        'quiet': True,
                        'no_warnings': True,
                        # 增强反检测措施
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': '*/*',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive',
                            'Referer': 'https://www.youtube.com/',
                            'Origin': 'https://www.youtube.com',
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors',
                            'Sec-Fetch-Site': 'cross-site',
                        },
                        'extractor_retries': 2,
                        'sleep_interval': 2,
                        'socket_timeout': 30,
                        'skip_unavailable_fragments': True,
                        'extractor_args': {
                            'youtube': {
                                'skip': ['dash'],  # 跳过DASH格式
                                'player_skip': ['configs'],
                            }
                        }
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if not info:
                            continue
                        
                        # 获取音频URL
                        audio_url = info.get('url')
                        video_title = info.get('title', 'Unknown Video')
                        
                        if audio_url:
                            print(f"Successfully got audio URL with format: {format_str}")
                            print(f"Got audio URL: {audio_url[:100]}...")
                            return audio_url, video_title
                            
                except Exception as format_error:
                    print(f"Format {format_str} failed: {format_error}")
                    continue
            
            raise Exception("所有音频格式提取尝试都失败了")
                
        except Exception as e:
            print(f"Audio URL extraction error: {e}")
            raise Exception(f"音频URL提取失败: {str(e)}")

    def transcribe_from_url(self, audio_url, client):
        """Transcribe audio from direct URL using OpenAI Whisper"""
        try:
            print(f"Downloading audio from URL for transcription...")
            
            # 下载音频到临时文件
            import urllib.request
            import tempfile
            
            # 创建临时文件
            temp_audio = tempfile.NamedTemporaryFile(suffix='.m4a', delete=False)
            temp_audio.close()
            
            # 下载音频
            urllib.request.urlretrieve(audio_url, temp_audio.name)
            
            print(f"Audio downloaded to temp file: {temp_audio.name}")
            
            # 使用现有的转录方法
            segments = self.transcribe_audio(temp_audio.name, client)
            
            # 清理临时文件
            try:
                os.remove(temp_audio.name)
                print(f"Cleaned up temp audio file")
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")
            
            return segments
            
        except Exception as e:
            print(f"URL transcription error: {e}")
            return [{
                "start": 0,
                "end": 5,
                "text": f"URL transcription failed: {str(e)}"
            }]

    def transcribe_audio(self, audio_file, client):
        """Transcribe using OpenAI Whisper"""
        try:
            # 获取文件扩展名
            file_ext = os.path.splitext(audio_file)[1].lower()
            
            # OpenAI支持的格式
            supported_formats = ['.mp3', '.mp4', '.m4a', '.wav', '.webm', '.mpeg', '.mpga']
            
            if file_ext not in supported_formats:
                print(f"Warning: File format {file_ext} may not be supported")
            
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
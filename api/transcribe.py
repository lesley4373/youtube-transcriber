from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import yt_dlp
from openai import OpenAI
from googletrans import Translator
import math

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
            "version": "2.0.0-ai"
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
            
            if not api_key:
                # Return demo data if no API key
                self.send_demo_response(url)
                return
            
            try:
                # Download audio from YouTube
                audio_file = self.download_audio(url)
                
                if not audio_file:
                    self.send_error_response(500, "Failed to download audio")
                    return
                
                # Transcribe with Whisper
                segments = self.transcribe_audio(audio_file, api_key)
                
                # Translate to Chinese
                translated_segments = self.translate_segments(segments)
                
                # Get video title
                title = self.get_video_title(url)
                
                # Send success response
                response = {
                    "title": title,
                    "segments": translated_segments
                }
                
                self.send_success_response(response)
                
                # Clean up temp file
                if audio_file and os.path.exists(audio_file):
                    os.remove(audio_file)
                    
            except Exception as e:
                self.send_error_response(500, f"Processing error: {str(e)}")
                
        except Exception as e:
            self.send_error_response(500, f"Request error: {str(e)}")
    
    def download_audio(self, url):
        """Download audio from YouTube video"""
        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, 'audio.mp3')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'audio_format': 'mp3',
                'max_filesize': 25 * 1024 * 1024  # 25MB limit for Vercel
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Check if file exists and is under size limit
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 25 * 1024 * 1024:
                    os.remove(output_path)
                    return None
                return output_path
            
            # Try to find the downloaded file
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    return os.path.join(temp_dir, file)
            
            return None
            
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def transcribe_audio(self, audio_file, api_key):
        """Transcribe audio using OpenAI Whisper API"""
        try:
            client = OpenAI(api_key=api_key)
            
            with open(audio_file, 'rb') as audio:
                # Use Whisper API with timestamps
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Process segments
            segments = []
            if hasattr(response, 'segments'):
                for seg in response.segments:
                    segments.append({
                        "start": seg.get('start', 0),
                        "end": seg.get('end', 0),
                        "text": seg.get('text', '').strip()
                    })
            else:
                # Fallback if no segments
                text = response.text if hasattr(response, 'text') else str(response)
                segments.append({
                    "start": 0,
                    "end": 10,
                    "text": text
                })
            
            return segments
            
        except Exception as e:
            print(f"Transcription error: {e}")
            # Return error as demo segment
            return [{
                "start": 0,
                "end": 5,
                "text": f"Transcription failed: {str(e)}"
            }]
    
    def translate_segments(self, segments):
        """Translate segments to Chinese"""
        try:
            translator = Translator()
            translated = []
            
            for seg in segments:
                try:
                    # Translate text to Chinese
                    translation = translator.translate(seg['text'], dest='zh-cn')
                    translated.append({
                        "start": seg['start'],
                        "end": seg['end'],
                        "text": seg['text'],
                        "translation": translation.text
                    })
                except Exception as e:
                    # If translation fails, use original text
                    translated.append({
                        "start": seg['start'],
                        "end": seg['end'],
                        "text": seg['text'],
                        "translation": seg['text']  # Fallback to original
                    })
            
            return translated
            
        except Exception as e:
            print(f"Translation error: {e}")
            # Return segments without translation
            return [{
                "start": seg['start'],
                "end": seg['end'],
                "text": seg['text'],
                "translation": "[Translation unavailable]"
            } for seg in segments]
    
    def get_video_title(self, url):
        """Get video title from YouTube"""
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('title', 'Unknown Video')
        except:
            return "YouTube Video"
    
    def send_demo_response(self, url):
        """Send demo response when no API key is provided"""
        title = self.get_video_title(url) if 'youtu' in url.lower() else "Demo Video"
        
        response = {
            "title": f"[DEMO - Need API Key] {title}",
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Please provide OpenAI API key for real transcription.",
                    "translation": "请提供OpenAI API密钥以进行真实转写。"
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
    
    def send_success_response(self, data):
        """Send successful response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        
        error_response = {
            "error": message,
            "code": code
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
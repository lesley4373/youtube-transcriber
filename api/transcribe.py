from http.server import BaseHTTPRequestHandler
import json
import yt_dlp

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 设置CORS头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            # 读取请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url')
            else:
                url = None
            
            if not url:
                error_response = {"error": "URL is required"}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return
            
            # 获取视频信息
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Video')
            except Exception:
                title = "Video (Unable to fetch title)"
            
            # 返回演示数据
            response = {
                "title": f"[DEMO] {title}",
                "segments": [
                    {
                        "start": 0.0,
                        "end": 5.0,
                        "text": "Hello, this is a demo transcription.",
                        "translation": "你好，这是一个演示转写结果。"
                    },
                    {
                        "start": 5.0,
                        "end": 10.0,
                        "text": "The deployment is working correctly!",
                        "translation": "部署工作正常！"
                    },
                    {
                        "start": 10.0,
                        "end": 15.0,
                        "text": "AI transcription will be added soon.",
                        "translation": "AI转写功能即将添加。"
                    }
                ]
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "message": "Error processing video"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_GET(self):
        # 健康检查
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "YouTube Transcriber API",
            "status": "healthy", 
            "version": "1.0.0-vercel"
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
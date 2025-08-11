from http.server import BaseHTTPRequestHandler
import json


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
            "version": "1.0.0-vercel"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            data = json.loads(body.decode())
            
            # Get the URL from request
            url = data.get('url', '')
            
            # Create demo response
            title = "YouTube Video (Demo Mode)" if 'youtu' in url.lower() else "Demo Video"
            
            response = {
                "title": f"[DEMO] {title}",
                "segments": [
                    {
                        "start": 0.0,
                        "end": 5.0,
                        "text": "Welcome! This is a demo transcription.",
                        "translation": "欢迎！这是一个演示转写结果。"
                    },
                    {
                        "start": 5.0,
                        "end": 10.0,
                        "text": "The deployment is working perfectly!",
                        "translation": "部署工作完美运行！"
                    },
                    {
                        "start": 10.0,
                        "end": 15.0,
                        "text": "Real AI transcription coming soon.",
                        "translation": "真实AI转写功能即将推出。"
                    },
                    {
                        "start": 15.0,
                        "end": 20.0,
                        "text": "Thank you for testing our application.",
                        "translation": "感谢您测试我们的应用程序。"
                    }
                ]
            }
            
            # Send successful response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "message": "Error processing request"
            }
            self.wfile.write(json.dumps(error_response).encode())
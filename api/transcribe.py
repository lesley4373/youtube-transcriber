import json

def handler(request, response):
    """
    Vercel serverless function handler
    """
    # Handle CORS
    response.status_code = 200
    response.headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return response
    
    # Handle GET request for health check
    if request.method == 'GET':
        response.body = json.dumps({
            "message": "YouTube Transcriber API",
            "status": "healthy",
            "version": "1.0.0-vercel"
        })
        return response
    
    # Handle POST request for transcription
    if request.method == 'POST':
        try:
            # Parse request body
            body = json.loads(request.body) if request.body else {}
            url = body.get('url', '')
            
            # Simple title extraction from URL
            title = "YouTube Video"
            if 'youtu' in url.lower():
                title = "YouTube Video (Demo Mode)"
            
            # Return demo transcription data
            result = {
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
            
            response.body = json.dumps(result)
            
        except Exception as e:
            response.status_code = 500
            response.body = json.dumps({
                "error": str(e),
                "message": "Error processing request"
            })
    
    return response
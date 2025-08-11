import json
import yt_dlp
from urllib.parse import parse_qs

def handler(request):
    # 设置CORS头
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # 处理GET请求 - 健康检查
    if request.method == 'GET':
        response = {
            "message": "YouTube Transcriber API",
            "status": "healthy",
            "version": "1.0.0-vercel"
        }
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response)
        }
    
    # 处理POST请求 - 转写视频
    if request.method == 'POST':
        try:
            # 解析请求数据
            if hasattr(request, 'get_json'):
                data = request.get_json()
            else:
                body = request.body if hasattr(request, 'body') else request.data
                if isinstance(body, bytes):
                    body = body.decode('utf-8')
                data = json.loads(body)
            
            url = data.get('url')
            
            if not url:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({"error": "URL is required"})
                }
            
            # 获取视频信息
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Video')
            except Exception as yt_error:
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
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response)
            }
            
        except Exception as e:
            error_response = {
                "error": str(e),
                "message": "Error processing video"
            }
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps(error_response)
            }
    
    # 不支持的方法
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps({"error": "Method not allowed"})
    }
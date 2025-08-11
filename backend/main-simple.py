from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import tempfile
from typing import List, Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    translation: str

class TranscriptResponse(BaseModel):
    title: str
    segments: List[TranscriptSegment]

def download_video_info(url: str) -> str:
    """获取视频信息，暂不下载"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'Unknown')
        return title

@app.get("/")
def read_root():
    return {
        "message": "YouTube Transcriber API", 
        "status": "healthy",
        "version": "1.0.0-simple",
        "note": "Simplified version for deployment testing",
        "endpoints": {
            "transcribe": "/transcribe",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_video(request: VideoRequest):
    try:
        print(f"Processing URL: {request.url}")
        
        # 获取视频标题
        title = download_video_info(request.url)
        
        # 返回模拟的转写结果（用于测试部署）
        demo_segments = [
            TranscriptSegment(
                start=0.0,
                end=5.0,
                text="Hello, this is a demo transcription.",
                translation="你好，这是一个演示转写结果。"
            ),
            TranscriptSegment(
                start=5.0,
                end=10.0,
                text="The full AI transcription feature will be available soon.",
                translation="完整的AI转写功能即将推出。"
            ),
            TranscriptSegment(
                start=10.0,
                end=15.0,
                text="Thank you for testing our deployment!",
                translation="感谢您测试我们的部署！"
            )
        ]
        
        return TranscriptResponse(
            title=f"[DEMO] {title}",
            segments=demo_segments
        )
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
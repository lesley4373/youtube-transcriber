from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import whisper
from googletrans import Translator
import os
import tempfile
import json
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

whisper_model = None
translator = Translator()

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
    return whisper_model

def download_audio(url: str) -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'audio.mp3')
        
        ydl_opts = {
            'format': 'worstaudio/worst',  # Use lower quality to avoid 403
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': output_path.replace('.mp3', '.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'cookiefile': 'cookies.txt',  # Optional: use cookies if available
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referer': 'https://www.youtube.com/',
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            
            audio_file = output_path
            if not os.path.exists(audio_file):
                for file in os.listdir(temp_dir):
                    if file.endswith('.mp3'):
                        audio_file = os.path.join(temp_dir, file)
                        break
            
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            new_temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            new_temp_file.write(audio_data)
            new_temp_file.close()
            
            return new_temp_file.name, title

def transcribe_audio(audio_path: str) -> List[Dict]:
    model = get_whisper_model()
    result = model.transcribe(audio_path, language='en')
    return result['segments']

def translate_text(text: str, target_lang: str = 'zh-cn') -> str:
    try:
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

@app.get("/")
def read_root():
    return {
        "message": "YouTube Transcriber API", 
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "transcribe": "/transcribe",
            "health": "/"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_video(request: VideoRequest):
    try:
        print(f"Processing URL: {request.url}")
        
        # Add timeout and better error handling
        try:
            audio_path, title = download_audio(request.url)
        except Exception as e:
            print(f"Download error: {e}")
            if "403" in str(e) or "Forbidden" in str(e):
                raise HTTPException(status_code=403, detail="YouTube access denied. Please try a different video or use a shorter video.")
            elif "timed out" in str(e).lower():
                raise HTTPException(status_code=408, detail="Download timeout. Please try a shorter video.")
            else:
                raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")
        
        try:
            segments = transcribe_audio(audio_path)
            
            formatted_segments = []
            for segment in segments:
                translation = translate_text(segment['text'])
                formatted_segments.append(TranscriptSegment(
                    start=segment['start'],
                    end=segment['end'],
                    text=segment['text'].strip(),
                    translation=translation
                ))
            
            return TranscriptResponse(
                title=title,
                segments=formatted_segments
            )
        
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
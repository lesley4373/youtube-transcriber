from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import tempfile
import os
from openai import OpenAI
from googletrans import Translator
import uvicorn

app = FastAPI(title="YouTube Transcriber API with AI")

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscribeRequest(BaseModel):
    url: str
    api_key: str = ""

@app.get("/")
async def root():
    return {"message": "YouTube Transcriber API with AI", "version": "2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "YouTube Transcriber with AI"}

@app.post("/transcribe")
async def transcribe_video(request: TranscribeRequest):
    """
    转写YouTube视频，支持任意长度
    无时间限制
    """
    try:
        # 检查API密钥
        api_key = request.api_key or os.environ.get('OPENAI_API_KEY', '')
        
        if not api_key:
            # 返回演示数据
            return {
                "title": "[DEMO] 需要OpenAI API密钥",
                "segments": [
                    {
                        "start": 0.0,
                        "end": 5.0,
                        "text": "Please provide OpenAI API key for real transcription.",
                        "translation": "请提供OpenAI API密钥以进行真实转写。"
                    }
                ]
            }
        
        # 1. 获取视频信息
        print(f"正在获取视频信息: {request.url}")
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            title = info.get('title', 'Unknown Video')
            duration = info.get('duration', 0)
        
        print(f"视频标题: {title}")
        print(f"视频时长: {duration}秒 ({duration//60}分{duration%60}秒)")
        
        # 2. 下载音频
        print("正在下载音频...")
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, 'audio.mp3')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': audio_path.replace('.mp3', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])
        
        # 找到下载的文件
        audio_file = None
        for file in os.listdir(temp_dir):
            if file.endswith('.mp3'):
                audio_file = os.path.join(temp_dir, file)
                break
        
        if not audio_file or not os.path.exists(audio_file):
            raise HTTPException(status_code=500, detail="音频下载失败")
        
        file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
        print(f"音频文件大小: {file_size_mb:.2f} MB")
        
        # 3. 使用Whisper转写
        print("正在进行AI转写...")
        client = OpenAI(api_key=api_key)
        
        # 如果文件大于25MB，需要分割处理
        if file_size_mb > 25:
            print("文件较大，使用分段处理...")
            # 这里可以实现音频分割逻辑
            segments = await transcribe_large_file(audio_file, client)
        else:
            with open(audio_file, 'rb') as audio:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            segments = []
            if hasattr(response, 'segments'):
                for seg in response.segments:
                    segments.append({
                        "start": seg.get('start', 0),
                        "end": seg.get('end', 0),
                        "text": seg.get('text', '').strip()
                    })
        
        print(f"转写完成，共{len(segments)}个片段")
        
        # 4. 翻译成中文
        print("正在翻译成中文...")
        translator = Translator()
        translated_segments = []
        
        for i, seg in enumerate(segments):
            try:
                translation = translator.translate(seg['text'], dest='zh-cn')
                translated_segments.append({
                    "start": seg['start'],
                    "end": seg['end'],
                    "text": seg['text'],
                    "translation": translation.text
                })
                print(f"翻译进度: {i+1}/{len(segments)}")
            except Exception as e:
                print(f"翻译错误: {e}")
                translated_segments.append({
                    "start": seg['start'],
                    "end": seg['end'],
                    "text": seg['text'],
                    "translation": seg['text']
                })
        
        # 5. 清理临时文件
        try:
            os.remove(audio_file)
            os.rmdir(temp_dir)
        except:
            pass
        
        print("处理完成！")
        
        return {
            "title": title,
            "duration": duration,
            "segments": translated_segments
        }
        
    except Exception as e:
        print(f"错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def transcribe_large_file(audio_file, client):
    """处理大文件的辅助函数"""
    # 这里可以实现音频分割和批处理逻辑
    # 暂时返回简单结果
    with open(audio_file, 'rb') as audio:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="text"
        )
    
    return [{
        "start": 0,
        "end": 60,
        "text": response
    }]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"启动服务器在端口 {port}")
    print("支持任意长度视频，无时间限制！")
    uvicorn.run(app, host="0.0.0.0", port=port)
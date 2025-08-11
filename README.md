# 🎥 YouTube Video Transcriber

AI-powered YouTube video transcription with bilingual (English-Chinese) translation and timestamps.

## ✨ Features

- 🎯 **YouTube Video Support**: Paste any YouTube URL
- 🤖 **AI Transcription**: Powered by OpenAI Whisper
- 🌍 **Bilingual Translation**: English audio → Chinese translation
- ⏱️ **Precise Timestamps**: Navigate to specific moments
- 📱 **Mobile Responsive**: Works on all devices
- 🎨 **Beautiful UI**: Clean, modern interface

## 🌐 Live Demo

**🔗 [Try it now!](https://your-app-url.vercel.app)**

## 🚀 Quick Start

### Online Usage (Recommended)

Just visit the live demo link above and start transcribing!

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/youtube-transcriber.git
cd youtube-transcriber
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

4. **Install FFmpeg**
- Mac: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: Download from https://ffmpeg.org/

## 📦 One-Click Deploy

### Deploy to Vercel (Frontend)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/youtube-transcriber)

### Deploy to Railway (Backend)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/youtube-transcriber)

### Deploy with Docker
```bash
docker-compose up -d
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python
- **Frontend**: React, Axios
- **AI**: OpenAI Whisper
- **Translation**: Google Translate
- **Video Processing**: yt-dlp, FFmpeg

## 📸 Screenshots

![Main Interface](screenshots/main.png)
![Transcription Result](screenshots/result.png)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube video processing
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://reactjs.org/) for the frontend framework

## 📞 Support

If you have any questions or issues, please [open an issue](https://github.com/yourusername/youtube-transcriber/issues) on GitHub.

---

⭐ If this project helped you, please consider giving it a star on GitHub!
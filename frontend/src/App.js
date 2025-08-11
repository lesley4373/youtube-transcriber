import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [subtitleText, setSubtitleText] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState(null);
  const [error, setError] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [inputMode, setInputMode] = useState('url'); // 'url', 'file', or 'text'

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setTranscript(null);

    try {
      // 动态获取API地址 - 支持Vercel全栈部署
      const apiUrl = process.env.REACT_APP_API_URL 
        ? `${process.env.REACT_APP_API_URL}/transcribe`
        : (window.location.hostname === 'localhost' 
          ? `http://${window.location.hostname}:8000/transcribe`
          : `/api/transcribe`);
      
      console.log('API URL:', apiUrl);
      console.log('Input mode:', inputMode);
      
      let response;
      if (inputMode === 'file' && audioFile) {
        console.log('Processing file:', audioFile.name, 'Size:', audioFile.size);
        
        // 检查文件大小 (限制25MB)
        if (audioFile.size > 25 * 1024 * 1024) {
          throw new Error('文件太大，请选择25MB以内的文件');
        }
        
        // 将文件转换为base64
        console.log('Converting file to base64...');
        const reader = new FileReader();
        const base64Promise = new Promise((resolve, reject) => {
          reader.onload = () => {
            console.log('File converted to base64, length:', reader.result.length);
            resolve(reader.result);
          };
          reader.onerror = (error) => {
            console.error('FileReader error:', error);
            reject(error);
          };
          reader.readAsDataURL(audioFile);
        });
        
        const base64Data = await base64Promise;
        
        console.log('Sending request with base64 data...');
        // 发送base64数据
        response = await axios.post(apiUrl, {
          audio_base64: base64Data,
          filename: audioFile.name,
          api_key: apiKey
        }, {
          timeout: 300000 // 5分钟超时
        });
      } else if (inputMode === 'text' && subtitleText) {
        console.log('Processing subtitle text...');
        // 字幕文本
        response = await axios.post(apiUrl, {
          subtitle_text: subtitleText,
          api_key: apiKey
        }, {
          timeout: 60000 // 1分钟超时
        });
      } else {
        console.log('Processing YouTube URL:', url);
        // YouTube URL
        response = await axios.post(apiUrl, { 
          url: url,
          api_key: apiKey 
        }, {
          timeout: 300000 // 5分钟超时
        });
      }
      
      console.log('Response received:', response.data);
      setTranscript(response.data);
    } catch (err) {
      console.error('Error details:', err);
      console.error('Error response:', err.response);
      
      let errorMessage = 'An error occurred while processing';
      
      if (err.message) {
        errorMessage = err.message;
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.status) {
        errorMessage = `HTTP ${err.response.status}: ${err.response.statusText}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>YouTube Video Transcriber</h1>
        <p>Convert YouTube videos to bilingual transcripts with timestamps</p>
      </header>

      <main>
        <div className="input-mode-selector">
          <button 
            type="button"
            className={inputMode === 'url' ? 'active' : ''}
            onClick={() => setInputMode('url')}
          >
            YouTube URL
          </button>
          <button 
            type="button"
            className={inputMode === 'file' ? 'active' : ''}
            onClick={() => setInputMode('file')}
          >
            Upload Audio
          </button>
          <button 
            type="button"
            className={inputMode === 'text' ? 'active' : ''}
            onClick={() => setInputMode('text')}
          >
            Paste Subtitles
          </button>
        </div>

        <form onSubmit={handleSubmit} className="url-form">
          {inputMode === 'url' ? (
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter YouTube video URL..."
              required
              className="url-input"
            />
          ) : inputMode === 'file' ? (
            <input
              type="file"
              onChange={(e) => setAudioFile(e.target.files[0])}
              accept="audio/*,video/*"
              required
              className="file-input"
            />
          ) : (
            <div className="subtitle-input-container">
              <textarea
                value={subtitleText}
                onChange={(e) => setSubtitleText(e.target.value)}
                placeholder="Paste YouTube subtitles here...
Example format:
0:00 Hello everyone
0:05 Welcome to this video
0:10 Today we will learn..."
                required
                className="subtitle-textarea"
                rows="8"
              />
              <div className="subtitle-help">
                <p><strong>How to get YouTube subtitles:</strong></p>
                <p>1. Open video → Click CC button → Right-click subtitle → Copy text</p>
                <p>2. Or use browser extensions to extract subtitles</p>
              </div>
            </div>
          )}
          <div className="api-key-section">
            <input
              type={showApiKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="OpenAI API Key (optional for demo)"
              className="api-key-input"
            />
            <button 
              type="button" 
              onClick={() => setShowApiKey(!showApiKey)}
              className="toggle-btn"
            >
              {showApiKey ? '🙈' : '👁️'}
            </button>
          </div>
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Processing...' : 'Transcribe'}
          </button>
        </form>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Downloading and processing video... This may take a few minutes.</p>
          </div>
        )}

        {transcript && (
          <div className="transcript-container">
            <h2>{transcript.title}</h2>
            <div className="segments">
              {transcript.segments.map((segment, index) => (
                <div key={index} className="segment">
                  <div className="timestamp">
                    [{formatTime(segment.start)} - {formatTime(segment.end)}]
                  </div>
                  <div className="text-container">
                    <div className="english-text">{segment.text}</div>
                    <div className="chinese-text">{segment.translation}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
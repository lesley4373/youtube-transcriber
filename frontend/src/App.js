import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState(null);
  const [error, setError] = useState('');

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
      // 动态获取API地址 - 支持生产环境
      const apiUrl = process.env.REACT_APP_API_URL 
        ? `${process.env.REACT_APP_API_URL}/transcribe`
        : `http://${window.location.hostname}:8000/transcribe`;
      
      const response = await axios.post(apiUrl, { url });
      setTranscript(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while processing the video');
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
        <form onSubmit={handleSubmit} className="url-form">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter YouTube video URL..."
            required
            className="url-input"
          />
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
import React, { useRef, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Download, ExternalLink, Video, ShoppingBag, Volume2, VolumeX } from 'lucide-react';

const VideoStep = ({ videoUrl, productUrl, script }) => {
  const videoRef = useRef(null);
  const [showShopNow, setShowShopNow] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  // Build timed narration schedule from script scenes
  const scenes = script?.scenes || [];

  // Web Speech API narration: speak voiceover at video time
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !ttsEnabled || scenes.length === 0) return;

    let spokenScenes = new Set();

    const handleTimeUpdate = () => {
      const t = video.currentTime;
      const duration = video.duration || 1;
      const sceneDuration = duration / scenes.length;

      scenes.forEach((scene, idx) => {
        const sceneStart = idx * sceneDuration;
        if (t >= sceneStart && !spokenScenes.has(idx)) {
          spokenScenes.add(idx);
          if (window.speechSynthesis && scene.voiceover) {
            window.speechSynthesis.cancel(); // cancel previous
            const utter = new SpeechSynthesisUtterance(scene.voiceover);
            utter.lang = 'hi-IN';
            utter.rate = 1.1;
            utter.pitch = 1;
            utter.onstart = () => setSpeaking(true);
            utter.onend = () => setSpeaking(false);
            window.speechSynthesis.speak(utter);
          }
        }
      });
    };

    const handleEnded = () => {
      window.speechSynthesis?.cancel();
      setSpeaking(false);
      setShowShopNow(true);
    };

    const handlePause = () => {
      window.speechSynthesis?.pause();
    };

    const handlePlay = () => {
      window.speechSynthesis?.resume();
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('pause', handlePause);
    video.addEventListener('play', handlePlay);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('play', handlePlay);
      window.speechSynthesis?.cancel();
    };
  }, [ttsEnabled, scenes]);

  // Also show Shop Now at end even without TTS
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const handleEnded = () => setShowShopNow(true);
    video.addEventListener('ended', handleEnded);
    return () => video.removeEventListener('ended', handleEnded);
  }, []);

  if (!videoUrl) {
    return (
      <div className="error-container">
        <Video size={48} color="#ef4444" />
        <h3>Video Not Found</h3>
        <p>There was an error retrieving the generated video.</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="video-container"
    >
      <div className="video-header">
        <div className="icon-badge">
          <Video size={24} />
        </div>
        <h2>Your Ad is Ready!</h2>
        <p className="subtitle">Preview your AI-generated advertisement below.</p>
      </div>

      {/* Video + Shop Now Overlay Wrapper */}
      <div className="video-preview-wrapper glass" style={{ position: 'relative' }}>
        <video
          ref={videoRef}
          controls
          className="main-video"
          src={videoUrl}
          onPlay={() => setShowShopNow(false)}
        >
          Your browser does not support the video tag.
        </video>

        {/* SHOP NOW OVERLAY */}
        {showShopNow && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="shop-now-overlay"
          >
            <motion.a
              href={productUrl || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="shop-now-btn"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.96 }}
            >
              <ShoppingBag size={22} />
              Shop Now
            </motion.a>
          </motion.div>
        )}
      </div>

      {/* TTS Toggle */}
      <div className="tts-toggle" onClick={() => {
        setTtsEnabled(prev => {
          if (prev) window.speechSynthesis?.cancel();
          return !prev;
        });
      }}>
        {ttsEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
        <span>{ttsEnabled ? 'AI Narration: ON' : 'AI Narration: OFF'}</span>
        {speaking && <span className="speaking-dot" />}
      </div>

      {/* Action Buttons */}
      <div className="video-actions">
        <button
          onClick={async () => {
            try {
              const response = await fetch(videoUrl);
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `ad_video_${Date.now()}.mp4`;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
            } catch (e) {
              window.open(videoUrl, '_blank');
            }
          }}
          className="btn btn-primary"
          style={{
            background: 'var(--premium-gradient)',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            padding: '12px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontWeight: '600',
            cursor: 'pointer',
            flex: 1
          }}
        >
          <Download size={20} /> Download MP4
        </button>

        {productUrl && (
          <a
            href={productUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn"
            style={{
              background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              padding: '12px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontWeight: '700',
              cursor: 'pointer',
              textDecoration: 'none',
              flex: 1
            }}
          >
            <ShoppingBag size={20} /> Shop Now
          </a>
        )}

        <button
          className="btn"
          onClick={() => window.open(videoUrl, '_blank')}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'white',
            borderRadius: '12px',
            padding: '12px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          <ExternalLink size={20} /> Open in Tab
        </button>
      </div>

      {/* ── Star Rating & Feedback ── */}
      <div className="feedback-section glass">
        {feedbackSubmitted ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="feedback-success"
          >
            <span style={{ fontSize: '2rem' }}>&#10003;</span>
            <h4>Thank you for your feedback!</h4>
            <p>Your rating of {rating}/5 has been saved.</p>
          </motion.div>
        ) : (
          <>
            <h3 className="feedback-title">Rate this Ad</h3>
            <p className="feedback-subtitle">Help us improve by rating and sharing your thoughts</p>

            <div className="star-row">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  className={`star-btn ${star <= (hoverRating || rating) ? 'active' : ''}`}
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                >
                  &#9733;
                </button>
              ))}
              {rating > 0 && <span className="rating-label">{rating}/5</span>}
            </div>

            <textarea
              className="feedback-textarea"
              placeholder="What did you like? What could be better?"
              value={feedbackText}
              onChange={e => setFeedbackText(e.target.value)}
              rows={3}
            />

            <button
              className="btn submit-feedback-btn"
              disabled={rating === 0 || feedbackLoading}
              onClick={async () => {
                setFeedbackLoading(true);
                try {
                  const { default: api } = await import('../../services/api');
                  await api.post('/workflow/feedback', {
                    rating,
                    feedback_text: feedbackText,
                    video_url: videoUrl,
                  });
                  setFeedbackSubmitted(true);
                } catch (e) {
                  console.error('Feedback submission failed:', e);
                  alert('Could not submit feedback. Please try again.');
                }
                setFeedbackLoading(false);
              }}
            >
              {feedbackLoading ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </>
        )}
      </div>

      <style>{`
        .video-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
          width: 100%;
          max-width: 600px;
          margin: 0 auto;
          color: white;
        }
        .video-header { text-align: center; }
        .icon-badge {
          width: 48px;
          height: 48px;
          background: var(--premium-gradient);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 16px;
          color: white;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        .subtitle { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }
        .video-preview-wrapper {
          width: 100%;
          aspect-ratio: 9/16;
          max-height: 500px;
          border-radius: 20px;
          overflow: hidden;
          background: black;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid rgba(255, 255, 255, 0.1);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }
        .main-video {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        /* Shop Now Overlay */
        .shop-now-overlay {
          position: absolute;
          bottom: 60px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 20;
          display: flex;
          justify-content: center;
        }
        .shop-now-btn {
          display: flex;
          align-items: center;
          gap: 10px;
          background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
          color: white;
          font-size: 1.2rem;
          font-weight: 800;
          padding: 16px 36px;
          border-radius: 50px;
          text-decoration: none;
          box-shadow: 0 8px 30px rgba(34, 197, 94, 0.5);
          letter-spacing: 0.5px;
          white-space: nowrap;
        }

        /* TTS Toggle */
        .tts-toggle {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.82rem;
          color: rgba(255,255,255,0.55);
          cursor: pointer;
          padding: 6px 14px;
          border-radius: 50px;
          border: 1px solid rgba(255,255,255,0.1);
          transition: all 0.2s;
        }
        .tts-toggle:hover { background: rgba(255,255,255,0.05); color: white; }
        .speaking-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #22c55e;
          animation: blink 1s ease-in-out infinite;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.2; }
        }

        .video-actions {
          display: flex;
          gap: 12px;
          width: 100%;
          flex-wrap: wrap;
        }
        .error-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 300px;
          text-align: center;
          color: white;
        }

        /* Feedback Section */
        .feedback-section {
          width: 100%;
          padding: 24px;
          border-radius: 16px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.08);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }
        .feedback-title {
          margin: 0;
          font-size: 1.15rem;
          font-weight: 700;
          color: white;
        }
        .feedback-subtitle {
          margin: 0;
          font-size: 0.85rem;
          color: rgba(255,255,255,0.5);
        }
        .star-row {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .star-btn {
          background: none;
          border: none;
          font-size: 2rem;
          cursor: pointer;
          color: rgba(255,255,255,0.2);
          transition: all 0.15s;
          padding: 0 2px;
        }
        .star-btn:hover, .star-btn.active {
          color: #facc15;
          transform: scale(1.15);
        }
        .rating-label {
          margin-left: 8px;
          font-size: 0.9rem;
          font-weight: 700;
          color: #facc15;
        }
        .feedback-textarea {
          width: 100%;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px;
          padding: 12px 16px;
          color: white;
          font-size: 0.9rem;
          font-family: inherit;
          resize: vertical;
          outline: none;
          transition: border-color 0.2s;
        }
        .feedback-textarea:focus {
          border-color: #6366f1;
        }
        .feedback-textarea::placeholder {
          color: rgba(255,255,255,0.3);
        }
        .submit-feedback-btn {
          background: linear-gradient(135deg, #6366f1, #a855f7) !important;
          color: white !important;
          border: none !important;
          border-radius: 12px !important;
          padding: 10px 28px !important;
          font-weight: 700 !important;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        .submit-feedback-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .feedback-success {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          color: #4ade80;
          text-align: center;
        }
        .feedback-success h4 {
          margin: 0;
          font-size: 1.1rem;
          color: white;
        }
        .feedback-success p {
          margin: 0;
          font-size: 0.85rem;
          color: rgba(255,255,255,0.5);
        }
      `}</style>
    </motion.div>
  );
};

export default VideoStep;

import React, { useRef, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Download, ExternalLink, Video, ShoppingBag, Volume2, VolumeX } from 'lucide-react';

const runwayStyles = `
  .video-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    width: 100%;
    max-width: 700px;
    margin: 0 auto;
    color: white;
  }
  .video-header { text-align: center; }
  .icon-badge {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
    color: white;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  }
  .subtitle { color: rgba(255, 255, 255, 0.5); font-size: 0.9rem; }
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
  .runway-prompt-card {
    width: 100%;
    padding: 24px;
    border-radius: 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .prompt-header {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .prompt-badge {
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: white;
  }
  .prompt-badge.part-a {
    background: linear-gradient(135deg, #f59e0b, #ef4444);
  }
  .prompt-badge.part-b {
    background: linear-gradient(135deg, #22c55e, #06b6d4);
  }
  .prompt-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: rgba(255,255,255,0.7);
  }
  .prompt-scenes {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .scene-tag {
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.25);
  }
  .prompt-text {
    font-size: 0.88rem;
    line-height: 1.6;
    color: rgba(255,255,255,0.85);
    background: rgba(0,0,0,0.3);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 300px;
    overflow-y: auto;
  }
  .copy-btn {
    align-self: flex-end;
    padding: 8px 20px;
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: white;
    font-weight: 700;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .copy-btn:hover {
    transform: scale(1.03);
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
  }
  .visual-ctx p {
    margin: 6px 0;
    font-size: 0.82rem;
    line-height: 1.5;
    color: rgba(255,255,255,0.65);
  }
  .visual-ctx strong {
    color: rgba(255,255,255,0.9);
  }
`;

const VideoStep = ({ videoUrl, productUrl, script, runwayPrompts, visualContext }) => {
  const videoRef = useRef(null);
  const [showShopNow, setShowShopNow] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [copied, setCopied] = useState('');

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

  // ── Copy to clipboard helper ──
  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(''), 2000);
    });
  };

  // ── Runway Prompts Mode ──
  if (!videoUrl && runwayPrompts) {
    const partA = runwayPrompts.part_a;
    const partB = runwayPrompts.part_b;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="video-container"
      >
        <div className="video-header">
          <div className="icon-badge" style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)' }}>
            <Video size={24} />
          </div>
          <h2>Runway ML Prompts Ready!</h2>
          <p className="subtitle">Copy each prompt and paste into RunwayML to generate your 30-sec ad (2 x 15 sec).</p>
        </div>

        {/* Prompt Part A */}
        <div className="runway-prompt-card glass">
          <div className="prompt-header">
            <span className="prompt-badge part-a">Part A</span>
            <span className="prompt-label">{partA?.label || 'Emotional Setup (15 sec)'}</span>
          </div>
          {partA?.scenes_merged && (
            <div className="prompt-scenes">
              {partA.scenes_merged.map((s, i) => (
                <span key={i} className="scene-tag">{s}</span>
              ))}
            </div>
          )}
          <div className="prompt-text">{partA?.prompt}</div>
          <button
            className="copy-btn"
            onClick={() => copyToClipboard(partA?.prompt || '', 'A')}
          >
            {copied === 'A' ? 'Copied!' : 'Copy Prompt A'}
          </button>
        </div>

        {/* Prompt Part B */}
        <div className="runway-prompt-card glass">
          <div className="prompt-header">
            <span className="prompt-badge part-b">Part B</span>
            <span className="prompt-label">{partB?.label || 'Product Payoff (15 sec)'}</span>
          </div>
          {partB?.scenes_merged && (
            <div className="prompt-scenes">
              {partB.scenes_merged.map((s, i) => (
                <span key={i} className="scene-tag">{s}</span>
              ))}
            </div>
          )}
          <div className="prompt-text">{partB?.prompt}</div>
          <button
            className="copy-btn"
            onClick={() => copyToClipboard(partB?.prompt || '', 'B')}
          >
            {copied === 'B' ? 'Copied!' : 'Copy Prompt B'}
          </button>
        </div>

        {/* Visual Context Reference */}
        {visualContext && (
          <div className="runway-prompt-card glass" style={{ borderColor: 'rgba(99, 102, 241, 0.2)' }}>
            <div className="prompt-header">
              <span className="prompt-badge" style={{ background: 'linear-gradient(135deg, #6366f1, #818cf8)' }}>Reference</span>
              <span className="prompt-label">Visual Consistency Guide</span>
            </div>
            <div className="visual-ctx">
              <p><strong>Person:</strong> {visualContext.person_description}</p>
              <p><strong>Setting:</strong> {visualContext.setting}</p>
              <p><strong>Lighting:</strong> {visualContext.lighting}</p>
            </div>
          </div>
        )}

        {/* Open RunwayML Button */}
        <div className="video-actions">
          <a
            href="https://app.runwayml.com"
            target="_blank"
            rel="noopener noreferrer"
            className="btn"
            style={{
              background: 'var(--premium-gradient)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              padding: '14px 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontWeight: '700',
              cursor: 'pointer',
              textDecoration: 'none',
              flex: 1,
              fontSize: '1rem'
            }}
          >
            <ExternalLink size={20} /> Open RunwayML
          </a>
        </div>

        <style>{`
          ${runwayStyles}
        `}</style>
      </motion.div>
    );
  }

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
                  const { default: api } = await import('../services/api');
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

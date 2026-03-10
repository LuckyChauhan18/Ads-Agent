import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Video, Check, Loader2 } from 'lucide-react';

const RenderProgressOverlay = ({ active, scenes, message, failed }) => {
  const [progresses, setProgresses] = useState([]);

  useEffect(() => {
    if (active && scenes && scenes.length > 0) {
      // Initialize progress array (one for each scene)
      setProgresses(new Array(scenes.length).fill(0));

      // Simulate parallel rendering progress
      const interval = setInterval(() => {
        setProgresses(prev => {
          let allDone = true;
          const next = prev.map(p => {
            if (p >= 100) return 100;
            allDone = false;
            // Random increment between 0 and 3
            const inc = Math.random() * 3;
            // Add slight bias: earlier scenes might progress slightly faster
            return Math.min(100, p + inc);
          });

          if (allDone) {
            clearInterval(interval);
          }
          return next;
        });
      }, 500); // update every 500ms

      return () => clearInterval(interval);
    } else {
      setProgresses([]);
    }
  }, [active, scenes]);

  if (!active) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="render-overlay glass"
    >
      <div className="render-content">
        <Video size={48} className="render-icon" />
        <h2 className="render-title">{message || "Rendering Video..."}</h2>
        <p className="render-subtitle">Gemini Veo 3.1 is synthesizing your scenes in parallel.</p>

        <div className="progress-grid">
          {scenes.map((scene, idx) => {
            const pct = progresses[idx] || 0;
            const isDone = pct >= 100;
            const isStarted = pct > 0;

            return (
              <div key={idx} className="progress-card">
                <div className="circular-progress">
                  <svg viewBox="0 0 100 100">
                    {/* Background track */}
                    <circle
                      cx="50" cy="50" r="40"
                      fill="none"
                      stroke="rgba(255,255,255,0.1)"
                      strokeWidth="8"
                    />
                    {/* Progress stroke */}
                    <circle
                      cx="50" cy="50" r="40"
                      fill="none"
                      stroke={failed ? "#ef4444" : (isDone ? "#4ade80" : "#6366f1")}
                      strokeWidth="8"
                      strokeDasharray="251.2" /* 2 * pi * 40 */
                      strokeDashoffset={251.2 - (251.2 * pct / 100)}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="progress-value">
                    {failed ? (
                      <span className="error-icon" style={{ color: '#ef4444', fontWeight: 'bold', fontSize: '1.5rem' }}>X</span>
                    ) : isDone ? (
                      <Check size={28} color="#4ade80" strokeWidth={3} />
                    ) : (
                      <span className="pct-text">{Math.floor(pct)}%</span>
                    )}
                  </div>
                </div>

                <div className="scene-details">
                  <span className="scene-number">Scene {idx + 1}</span>
                  <span className="scene-intent">{scene.intent}</span>
                </div>
              </div>
            );
          })}
        </div>

        {progresses.length > 0 && progresses.every(p => p >= 100) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="merging-status-card"
          >
            <Loader2 size={24} className="merging-spinner" />
            <div className="merging-text">
              <h4>Merging Final Video</h4>
              <p>Stitching AI scenes together with smooth transitions...</p>
            </div>
          </motion.div>
        )}
      </div>

      <style>{`
        .render-overlay {
          position: absolute;
          inset: 0;
          z-index: 100;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background: rgba(15, 23, 42, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 24px;
        }
        .render-content {
          max-width: 800px;
          width: 90%;
          text-align: center;
          padding: 40px;
        }
        .render-icon {
          color: #6366f1;
          margin-bottom: 24px;
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.1); }
        }
        .render-title {
          font-size: 2rem;
          font-weight: 800;
          margin-bottom: 8px;
          background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .render-subtitle {
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 40px;
          font-size: 1.1rem;
        }
        .progress-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 24px;
          justify-content: center;
        }
        .progress-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 16px;
          padding: 20px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }
        .circular-progress {
          position: relative;
          width: 80px;
          height: 80px;
        }
        .circular-progress > svg {
          transform: rotate(-90deg);
          width: 100%;
          height: 100%;
        }
        .circular-progress circle {
          transition: stroke-dashoffset 0.5s ease-out;
        }
        .progress-value {
          position: absolute;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .pct-text {
          font-size: 0.9rem;
          font-weight: 700;
          color: rgba(255, 255, 255, 0.9);
        }
        .scene-details {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .scene-number {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: #6366f1;
          font-weight: 700;
        }
        .scene-intent {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.8);
          font-weight: 500;
          line-height: 1.2;
        }
        .merging-status-card {
          margin-top: 32px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.3);
          border-radius: 16px;
          padding: 20px 32px;
          display: flex;
          align-items: center;
          gap: 20px;
          box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
        }
        .merging-spinner {
          color: #a855f7;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .merging-text {
          text-align: left;
        }
        .merging-text h4 {
          margin: 0;
          font-size: 1.1rem;
          font-weight: 700;
          color: #fff;
        }
        .merging-text p {
          margin: 4px 0 0 0;
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.7);
        }
      `}</style>
    </motion.div>
  );
};

export default RenderProgressOverlay;

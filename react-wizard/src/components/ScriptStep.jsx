import React from 'react';
import { motion } from 'framer-motion';

const ScriptStep = ({ script, updateScene }) => {
  if (!script || !script.scenes) return <div className="loading-script">Generating storyboard...</div>;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="script-step"
    >
      <div className="header-info">
        <h2>Storyboard Script</h2>
        <p className="subtitle">Review and edit the AI-generated voiceover for each scene.</p>
      </div>

      <div className="storyboard-container">
        {script.scenes.map((s, i) => (
          <motion.div
            key={i}
            className="scene-card glass"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <div className="scene-header">
              <div className="scene-meta">
                <span className="scene-tag">Scene {i + 1}</span>
                <span className="intent-badge">{s.intent}</span>
              </div>
              <div className="scene-type">{s.scene}</div>
            </div>

            <div className="input-wrapper">
              <label>Voiceover Content</label>
              <textarea
                value={s.voiceover || ''}
                onChange={(e) => updateScene(i, e.target.value)}
                placeholder="The AI is still thinking of the perfect words..."
                className="voiceover-input"
              />
            </div>
          </motion.div>
        ))}
      </div>

      <style>{`
        .script-step {
          width: 100%;
          max-width: 900px;
          margin: 0 auto;
        }
        .header-info {
          margin-bottom: 32px;
          text-align: center;
        }
        .subtitle {
          color: rgba(255, 255, 255, 0.5);
          font-size: 0.95rem;
          margin-top: 8px;
        }
        .storyboard-container {
          display: flex;
          flex-direction: column;
          gap: 24px;
          max-height: 60vh;
          overflow-y: auto;
          padding: 10px 20px 20px 10px;
        }
        .storyboard-container::-webkit-scrollbar {
          width: 6px;
        }
        .storyboard-container::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 10px;
        }
        .storyboard-container::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .scene-card {
          padding: 24px;
          border-radius: 16px;
          border: 1px solid rgba(255, 255, 255, 0.08);
          transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .scene-card:hover {
          border-color: rgba(255, 255, 255, 0.2);
          transform: translateY(-2px);
        }
        .scene-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .scene-meta {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .scene-tag {
          font-size: 0.7rem;
          font-weight: 900;
          color: var(--emerald, #10b981);
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        .intent-badge {
          background: rgba(255, 255, 255, 0.05);
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .scene-type {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--amber, #f59e0b);
          opacity: 0.8;
        }
        .input-wrapper label {
          display: block;
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.4);
          margin-bottom: 8px;
          font-weight: 500;
        }
        .voiceover-input {
          width: 100%;
          min-height: 100px;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 16px;
          color: white;
          font-family: inherit;
          font-size: 1rem;
          line-height: 1.6;
          resize: vertical;
          transition: all 0.3s ease;
        }
        .voiceover-input:focus {
          outline: none;
          background: rgba(0, 0, 0, 0.3);
          border-color: var(--emerald, #10b981);
          box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
        }
        .loading-script {
          text-align: center;
          padding: 40px;
          color: rgba(255, 255, 255, 0.5);
        }
      `}</style>
    </motion.div>
  );
};

export default ScriptStep;

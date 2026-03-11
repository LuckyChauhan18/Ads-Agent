import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Layout, MessageSquare, Eye, User, Sparkles } from 'lucide-react';

const ReviewStep = ({ state, updateData }) => {
  const scenes = state.script?.scenes || [];
  const avatar = state.avatar;

  const handleSceneUpdate = (index, field, value) => {
    const newScenes = [...scenes];
    newScenes[index] = { ...newScenes[index], [field]: value };
    updateData({ script: { ...state.script, scenes: newScenes } });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="storyboard-review"
    >
      <div className="review-header">
        <Sparkles className="header-icon" />
        <h2>Final Storyboard</h2>
        <p className="subtitle">Review the visual continuity and narrative flow before rendering.</p>
      </div>

      <div className="config-overview card glass">
        <div className="overview-item">
          <User size={16} />
          <span>{avatar.gender} {avatar.style} Presenter</span>
        </div>
        <div className="overview-item">
          <MessageSquare size={16} />
          <span>{avatar.language} Delivery</span>
        </div>
        <div className="overview-item">
          <Layout size={16} />
          <span>{scenes.length} Strategic Scenes</span>
        </div>
      </div>

      <div className="scenes-timeline">
        {scenes.map((scene, i) => (
          <div key={i} className="scene-row glass">
            <div className="scene-meta">
              <span className="scene-number">Scene {i + 1}</span>
              <span className="scene-label">{scene.scene}</span>
            </div>

            <div className="scene-details">
              <div className="detail-block">
                <label><MessageSquare size={12} /> Narrative (Voiceover)</label>
                <textarea
                  className="voiceover-input"
                  value={scene.voiceover}
                  onChange={(e) => handleSceneUpdate(i, 'voiceover', e.target.value)}
                  placeholder="Enter voiceover text..."
                />
              </div>

              <div className="detail-block continuity">
                <label><Eye size={12} /> Visual Continuity Hint</label>
                <textarea
                  className="continuity-input"
                  value={scene.visual_continuity || ""}
                  onChange={(e) => handleSceneUpdate(i, 'visual_continuity', e.target.value)}
                  placeholder="Describe visual flow..."
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .storyboard-review {
          width: 100%;
          max-width: 900px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .review-header {
          text-align: center;
          margin-bottom: 8px;
        }
        .header-icon {
          width: 48px;
          height: 48px;
          color: #fcd34d;
          margin-bottom: 16px;
        }
        .config-overview {
          display: flex;
          justify-content: space-around;
          padding: 16px;
          border-radius: 16px;
        }
        .overview-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.7);
        }
        .scenes-timeline {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .scene-row {
          display: grid;
          grid-template-columns: 120px 1fr;
          padding: 20px;
          border-radius: 16px;
          border: 1px solid rgba(255, 255, 255, 0.05);
          background: rgba(255, 255, 255, 0.01);
        }
        .scene-meta {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .scene-number {
          font-size: 0.7rem;
          font-weight: 800;
          color: rgba(255, 255, 255, 0.3);
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        .scene-label {
          font-size: 1rem;
          font-weight: 700;
          color: #6366f1;
        }
        .scene-details {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        .detail-block label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.65rem;
          font-weight: 700;
          color: rgba(255, 255, 255, 0.4);
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        .voiceover-input, .continuity-input {
          width: 100%;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: white;
          padding: 10px;
          font-family: inherit;
          font-size: 0.9rem;
          line-height: 1.5;
          resize: vertical;
          min-height: 80px;
          transition: border-color 0.2s;
        }
        .voiceover-input:focus, .continuity-input:focus {
          outline: none;
          border-color: #6366f1;
          background: rgba(255, 255, 255, 0.08);
        }
        .continuity-input {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.7);
          font-style: italic;
        }
        .detail-block.continuity {
          background: rgba(0, 0, 0, 0.1);
          padding: 4px;
          border-radius: 8px;
        }
      `}</style>
    </motion.div>
  );
};

export default ReviewStep;

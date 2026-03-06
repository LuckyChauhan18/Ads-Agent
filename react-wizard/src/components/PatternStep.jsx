import React from 'react';
import { motion } from 'framer-motion';

const PatternStep = ({ blueprint, updateBlueprint }) => {
  if (!blueprint) return <div className="loading-pattern">Preparing your ad blueprint...</div>;

  const technical = blueprint.pattern_blueprint || {};

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="pattern-step"
    >
      <div className="header-info">
        <h2>Ad Blueprint</h2>
        <p className="subtitle">This strategy was crafted by analyzing your product against market winners.</p>
      </div>

      <div className="card glass pattern-editor">
        <div className="pattern-header">
          <span className="badge">Active Strategy</span>
          <input
            className="pattern-title-input"
            value={blueprint.pattern_name || ''}
            onChange={(e) => updateBlueprint({ pattern_name: e.target.value })}
            placeholder="Pattern Name"
          />
        </div>

        <div className="input-group full-width">
          <label>Strategic Goal</label>
          <textarea
            value={blueprint.strategic_goal || ''}
            onChange={(e) => updateBlueprint({ strategic_goal: e.target.value })}
            placeholder="What is the main goal of this pattern?"
            className="goal-textarea"
          />
        </div>

        <div className="blueprint-grid">
          <div className="detail-item">
            <span className="label">Hook Style</span>
            <input
              className="inline-input"
              value={technical.hook_type || ''}
              onChange={(e) => updateBlueprint({ pattern_blueprint: { ...technical, hook_type: e.target.value } })}
            />
          </div>
          <div className="detail-item">
            <span className="label">CTA Focus</span>
            <input
              className="inline-input"
              value={technical.cta || ''}
              onChange={(e) => updateBlueprint({ pattern_blueprint: { ...technical, cta: e.target.value } })}
            />
          </div>
          <div className="detail-item">
            <span className="label">Tone</span>
            <input
              className="inline-input"
              value={technical.tone || ''}
              onChange={(e) => updateBlueprint({ pattern_blueprint: { ...technical, tone: e.target.value } })}
            />
          </div>
          <div className="detail-item">
            <span className="label">Ad Angle</span>
            <input
              className="inline-input"
              value={technical.angle || ''}
              onChange={(e) => updateBlueprint({ pattern_blueprint: { ...technical, angle: e.target.value } })}
            />
          </div>
        </div>
      </div>

      <style>{`
        .pattern-step {
          width: 100%;
          max-width: 800px;
          margin: 0 auto;
        }
        .header-info {
          text-align: center;
          margin-bottom: 32px;
        }
        .subtitle {
          color: rgba(255, 255, 255, 0.4);
          font-size: 0.9rem;
          margin-top: 8px;
        }
        .pattern-editor {
          padding: 32px;
          display: flex;
          flex-direction: column;
          gap: 32px;
          border-radius: 24px;
        }
        .pattern-header {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .badge {
          background: var(--amber, #f59e0b);
          color: black;
          padding: 4px 12px;
          border-radius: 6px;
          font-size: 0.65rem;
          font-weight: 800;
          text-transform: uppercase;
          width: fit-content;
          letter-spacing: 0.5px;
        }
        .pattern-title-input {
          background: transparent;
          border: none;
          color: white;
          font-size: 1.5rem;
          font-weight: 700;
          width: 100%;
          outline: none;
          padding: 0;
          margin: 0;
        }
        .pattern-title-input:focus {
          border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        .goal-textarea {
          width: 100%;
          min-height: 120px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          padding: 16px;
          color: white;
          font-size: 1rem;
          line-height: 1.6;
          margin-top: 8px;
          outline: none;
          transition: var(--transition);
        }
        .goal-textarea:focus {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(255, 255, 255, 0.2);
        }
        .blueprint-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
          padding-top: 24px;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .detail-item .label {
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.4);
          text-transform: uppercase;
          letter-spacing: 0.8px;
          font-weight: 700;
        }
        .inline-input {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          padding: 8px 12px;
          color: white;
          font-size: 1rem;
          font-weight: 600;
          outline: none;
          transition: var(--transition);
        }
        .inline-input:focus {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(255, 255, 255, 0.2);
        }
        .loading-pattern {
          text-align: center;
          padding: 40px;
          color: rgba(255, 255, 255, 0.5);
        }
      `}</style>
    </motion.div>
  );
};

export default PatternStep;

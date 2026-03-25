import React from 'react';
import { motion } from 'framer-motion';

const PatternStep = ({ blueprint, updateBlueprint }) => {
  if (!blueprint) return <div className="loading-pattern">Preparing your ad blueprint...</div>;

  const technical = blueprint.creative_dna || {};

  const NARRATIVES = ["Problem -> Discovery -> Transformation", "Science Proof & Breakdown", "Lifestyle Routine / Day in the Life", "Social Proof Showcase", "Contrarian Belief Narrative", "Myth Busting / educational"];
  const HOOKS = ["Contrarian (Surprising/Counter-intuitive)", "Problem Disclosure", "Curiosity (Open Loop)", "Aspirational Future Visualization", "Vulnerable confession"];
  const VISUALS = ["Aesthetic Lifestyle", "Product Demonstration closeups", "Home Routine / GRWM style", "Dynamic B-Roll Montage"];
  const PROOFS = ["Product demonstration demo", "Before/After result", "Customer testimonial review"];
  const CTAS = ["Discover the Secret", "Try Now Risk-Free", "Claim limited offer", "See it working"];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="pattern-step"
    >
      <div className="header-info">
        <h2>Creative DNA</h2>
        <p className="subtitle">Structured strategy guidelines strictly aligned to your funnel goals.</p>
      </div>

      <div className="card glass pattern-editor">
        <div className="pattern-header">
          <span className="badge">Creative Direction</span>
          <div className="hook-line-box">
            <label className="label">Recommended Hook Sentence</label>
            <textarea
              className="inline-input full-width"
              value={technical.hook_line_recommendation || ''}
              onChange={(e) => updateBlueprint({ creative_dna: { ...technical, hook_line_recommendation: e.target.value } })}
              rows={2}
            />
          </div>
        </div>

        <div className="blueprint-grid">
          <div className="detail-item">
            <span className="label">Narrative Type</span>
            <select
              className="inline-input"
              value={technical.narrative_type || ''}
              onChange={(e) => updateBlueprint({ creative_dna: { ...technical, narrative_type: e.target.value } })}
            >
              <option value="">Select Narrative...</option>
              {NARRATIVES.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div className="detail-item">
            <span className="label">Hook Mechanism</span>
            <select
              className="inline-input"
              value={technical.hook_mechanism || ''}
              onChange={(e) => updateBlueprint({ creative_dna: { ...technical, hook_mechanism: e.target.value } })}
            >
              <option value="">Select Hook...</option>
              {HOOKS.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div className="detail-item">
            <span className="label">Visual Style</span>
            <select
              className="inline-input"
              value={technical.visual_style || ''}
              onChange={(e) => updateBlueprint({ creative_dna: { ...technical, visual_style: e.target.value } })}
            >
              <option value="">Select Visual...</option>
              {VISUALS.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div className="detail-item">
            <span className="label">Psychology Trigger</span>
            <select
              className="inline-input"
              value={technical.psychology_trigger || ''}
              onChange={(e) => updateBlueprint({ creative_dna: { ...technical, psychology_trigger: e.target.value } })}
            >
              <option value="">Select Trigger...</option>
              {["Curiosity", "Confidence", "Relief"].map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div className="detail-item">
            <span className="label">Proof Type</span>
            <select
              className="inline-input"
              value={technical.proof_type || ''}
              onChange={(e) => updateBlueprint({ creative_dna: { ...technical, proof_type: e.target.value } })}
            >
              <option value="">Select Proof...</option>
              {PROOFS.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div className="detail-item">
            <span className="label">CTA Type</span>
            <select
              className="inline-input"
              value={technical.cta_type || ''}
              onChange={(e) => updateBlueprint({ creative_dna: { ...technical, cta_type: e.target.value } })}
            >
              <option value="">Select CTA...</option>
              {CTAS.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
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

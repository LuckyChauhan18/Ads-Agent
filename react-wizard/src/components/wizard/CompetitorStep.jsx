import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Quote, Target, Wind, Zap, AlertCircle, CheckCircle2, Gift, MessageSquare, Gauge, Hash } from 'lucide-react';

const CompetitorStep = ({ research, updateCompetitor }) => {
  if (!research) return (
    <div className="loading-state">
      <div className="spinner" />
      <p>Analyzing competitor ecosystems...</p>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="step-content"
    >
      <div className="research-header">
        <div className="header-text">
          <h2>Market DNA Insights</h2>
          <p className="subtitle">Deep architectural breakdown of how your competitors are winning.</p>
        </div>
        <div className="ai-badge">
          <Brain size={14} />
          <span>Deep DNA Extraction Active</span>
        </div>
      </div>

      <div className="card-grid">
        {research.competitors.map((c, i) => {
          const primaryAd = c.ads && c.ads.length > 0 ? c.ads[0].dna : null;

          return (
            <div key={i} className="card glass dna-card">
              <div className="card-header">
                <div className="brand-info">
                  <h3>{c.company}</h3>
                  <div className="dna-tags">
                    <span className="tag tone">{primaryAd?.tone || 'Professional'}</span>
                    <span className="tag type">{primaryAd?.hook_type || 'Discovery'}</span>
                  </div>
                </div>
                <div className="count-badge">
                  <span className="actual">{c.actual_count}</span>
                  <span className="separator">/</span>
                  <span className="target">{c.target_count}</span>
                  <span className="label">DNA</span>
                </div>
              </div>

              <div className="card-body">
                {/* Core Copy Sections */}
                <div className="dna-main-grid">
                  <div className="dna-section highlight">
                    <div className="section-label"><Wind size={12} /><span>HOOK</span></div>
                    <div className="dna-content hook-text italic">{primaryAd?.refined_hook || primaryAd?.hook || "N/A"}</div>
                  </div>

                  <div className="dna-section highlight">
                    <div className="section-label"><Target size={12} /><span>PUNCH LINE</span></div>
                    <div
                      className="dna-content punchline-text editable-text"
                      contentEditable
                      onBlur={(e) => updateCompetitor(i, e.target.innerText)}
                      suppressContentEditableWarning={true}
                    >
                      {c.top_punchline}
                    </div>
                  </div>
                </div>

                {/* Strategy Breakdown */}
                <div className="strategy-matrix">
                  <div className="matrix-item">
                    <div className="matrix-label"><AlertCircle size={12} /><span>PROBLEM</span></div>
                    <div className="matrix-value">{primaryAd?.problem || "Implied/Contextual"}</div>
                  </div>
                  <div className="matrix-item">
                    <div className="matrix-label"><CheckCircle2 size={12} /><span>SOLUTION</span></div>
                    <div className="matrix-value">{primaryAd?.solution || "Product Benefits"}</div>
                  </div>
                  <div className="matrix-item">
                    <div className="matrix-label"><Gift size={12} /><span>OFFER</span></div>
                    <div className="matrix-value status-badge">{primaryAd?.offer || "None Detected"}</div>
                  </div>
                </div>

                {/* Footer Metadata */}
                <div className="footer-meta">
                  <div className="meta-pill">
                    <MessageSquare size={11} />
                    <span>{primaryAd?.angle || 'Lifestyle'} Angle</span>
                  </div>
                  <div className="meta-pill">
                    <Gauge size={11} />
                    <span>{primaryAd?.text_length || 'Medium'} chars</span>
                  </div>
                  <div className="meta-pill">
                    <Hash size={11} />
                    <span>Emojis: {primaryAd?.emoji_usage ? 'Yes' : 'No'}</span>
                  </div>
                  <div className="meta-pill premium">
                    <Zap size={11} />
                    <span>High Converting</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <style>{`
        .research-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 30px;
        }
        .subtitle {
          font-size: 0.95rem;
          color: rgba(255, 255, 255, 0.5);
          margin-top: 6px;
        }
        .ai-badge {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.2);
          padding: 8px 16px;
          border-radius: 30px;
          color: #a5b4fc;
          font-size: 0.8rem;
          font-weight: 600;
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.1);
        }
        
        .card-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
          gap: 24px;
        }
        .dna-card {
           padding: 0;
           overflow: hidden;
           border: 1px solid rgba(255, 255, 255, 0.08);
           background: rgba(255, 255, 255, 0.01);
           transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .dna-card:hover {
           transform: translateY(-4px);
           box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
           border-color: rgba(255, 255, 255, 0.15);
        }

        .card-header {
          padding: 24px;
          background: rgba(255, 255, 255, 0.02);
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .brand-info h3 {
          font-size: 1.3rem;
          margin-bottom: 8px;
          letter-spacing: -0.5px;
        }
        .dna-tags {
          display: flex;
          gap: 8px;
        }
        .tag {
          font-size: 0.6rem;
          padding: 3px 10px;
          border-radius: 6px;
          text-transform: uppercase;
          font-weight: 800;
          letter-spacing: 0.8px;
        }
        .tag.tone { background: rgba(34, 197, 94, 0.12); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.2); }
        .tag.type { background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.2); }

        .count-badge {
          display: flex;
          flex-direction: column;
          align-items: center;
          background: rgba(0, 0, 0, 0.2);
          padding: 8px 12px;
          border-radius: 12px;
          border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .count-badge .actual { font-weight: 900; color: #4ade80; font-size: 1.2rem; }
        .count-badge .target { opacity: 0.3; font-size: 0.75rem; margin-top: -2px; }
        .count-badge .label { font-size: 0.55rem; text-transform: uppercase; opacity: 0.5; margin-top: 4px; font-weight: 700; }

        .card-body {
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .dna-main-grid {
           display: grid;
           grid-template-columns: 1fr 1fr;
           gap: 16px;
        }

        .dna-section {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .section-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.65rem;
          font-weight: 800;
          color: rgba(255, 255, 255, 0.3);
          letter-spacing: 1.2px;
          text-transform: uppercase;
        }
        .dna-content {
          background: rgba(255, 255, 255, 0.02);
          border-radius: 14px;
          padding: 16px;
          font-size: 0.9rem;
          line-height: 1.5;
          color: rgba(255, 255, 255, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.03);
          min-height: 80px;
        }
        .dna-content.italic { font-style: italic; color: rgba(255, 255, 255, 0.7); }
        .punchline-text {
          font-weight: 600;
          color: white;
          background: rgba(99, 102, 241, 0.05);
          border: 1px solid rgba(99, 102, 241, 0.1);
        }

        .strategy-matrix {
           display: grid;
           grid-template-columns: repeat(3, 1fr);
           gap: 12px;
           background: rgba(255, 255, 255, 0.01);
           padding: 16px;
           border-radius: 16px;
           border: 1px solid rgba(255, 255, 255, 0.03);
        }
        .matrix-item {
           display: flex;
           flex-direction: column;
           gap: 6px;
        }
        .matrix-label {
           display: flex;
           align-items: center;
           gap: 4px;
           font-size: 0.6rem;
           font-weight: 700;
           color: rgba(255, 255, 255, 0.3);
        }
        .matrix-value {
           font-size: 0.8rem;
           color: rgba(255, 255, 255, 0.9);
           font-weight: 500;
        }
        .status-badge {
           color: #fcd34d;
           font-weight: 700;
        }

        .footer-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          padding-top: 12px;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        .meta-pill {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.7rem;
          color: rgba(255, 255, 255, 0.4);
          background: rgba(255, 255, 255, 0.03);
          padding: 6px 12px;
          border-radius: 20px;
          font-weight: 500;
          border: 1px solid transparent;
        }
        .meta-pill.premium {
           background: rgba(99, 102, 241, 0.1);
           color: #a5b4fc;
           border-color: rgba(99, 102, 241, 0.2);
        }

        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 300px;
          gap: 20px;
        }
        .spinner {
          width: 48px;
          height: 48px;
          border: 4px solid rgba(255, 255, 255, 0.05);
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: spin 1s cubic-bezier(0.5, 0, 0.5, 1) infinite;
          filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.3));
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </motion.div>
  );
};

export default CompetitorStep;

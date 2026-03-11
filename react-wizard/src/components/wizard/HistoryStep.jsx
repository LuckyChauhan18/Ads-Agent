import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { History, Calendar, Package, ArrowRight, Video, X, Sparkles, Instagram, Youtube, Facebook, Smartphone } from 'lucide-react';
import { workflowService } from '../../services/api';

const HistoryStep = ({ onClose }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  const getPlatformIcon = (platform) => {
    switch (platform?.toLowerCase()) {
      case 'instagram': return <Instagram size={14} />;
      case 'youtube': return <Youtube size={14} />;
      case 'facebook': return <Facebook size={14} />;
      default: return <Smartphone size={14} />;
    }
  };

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await workflowService.runGetHistory();
        setHistory(res.data.results || []);
      } catch (e) {
        console.error("Failed to fetch history", e);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="history-loading">
        <Sparkles className="animate-pulse" />
        <p>Retrieving your creative history...</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="history-overlay glass"
    >
      <div className="history-header">
        <div className="title-group">
          <History size={24} className="text-secondary" />
          <h2>Campaign History</h2>
        </div>
        <button className="close-btn" onClick={onClose}>
          <X size={20} />
        </button>
      </div>

      <div className="history-list">
        {history.length === 0 ? (
          <div className="empty-state">
            <Package size={48} opacity={0.2} />
            <p>No past campaigns found yet.</p>
          </div>
        ) : (
          history.map((item) => (
            <div
              key={item._id}
              className={`history-item glass ${selectedId === item._id ? 'expanded' : ''}`}
              onClick={() => setSelectedId(selectedId === item._id ? null : item._id)}
            >
              <div className="item-summary">
                <div className="item-info">
                  <h3>
                    {item.brand_name && item.product_name
                      ? `${item.brand_name} - ${item.product_name}`
                      : item.brand_name || item.product_name || "Untitled Campaign"}
                  </h3>
                  <div className="item-meta">
                    <Calendar size={12} />
                    <span>{item.timestamp ? new Date(item.timestamp).toLocaleDateString() : 'Recent'}</span>
                    <span className="platform-tag">
                      {getPlatformIcon(item.platform)} {item.platform || 'Unknown'}
                    </span>
                  </div>
                </div>
                <div className="item-badge">
                  {item.funnel_stage || item.campaign_psychology?.funnel_stage || 'Ad'}
                </div>
              </div>

              {selectedId === item._id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  className="item-details"
                >
                  <div className="details-grid">
                    <div className="detail-section">
                      <h4>Core Strategy</h4>
                      <p><strong>Goal:</strong> {item.campaign_psychology?.core_message || 'N/A'}</p>
                      <p><strong>Hook:</strong> {item.campaign_psychology?.hook_strategy?.angle || 'N/A'}</p>
                      {item.primary_emotions && item.primary_emotions.length > 0 && (
                        <div className="emotions-container">
                          {item.primary_emotions.map((emo, idx) => (
                            <span key={idx} className="emotion-tag">{emo}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    {item.pattern_blueprint && (
                      <div className="detail-section">
                        <h4>Ad Pattern</h4>
                        <p><strong>Style:</strong> {item.pattern_blueprint?.pattern_blueprint?.opening_style || 'N/A'}</p>
                      </div>
                    )}
                  </div>

                  {item.final_storyboard && item.final_storyboard.scenes && (
                    <div className="storyboard-section">
                      <h4>Final Storyboard</h4>
                      <div className="storyboard-scroller">
                        {item.final_storyboard.scenes.map((scene, idx) => (
                          <div key={idx} className="storyboard-scene glass">
                            <div className="scene-header">
                              <span className="scene-idx">Scene {idx + 1}</span>
                              <span className="scene-intent">{scene.intent}</span>
                            </div>
                            <p className="scene-voiceover">"{scene.voiceover || scene.copy}"</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          ))
        )}
      </div>

      <style>{`
        .history-overlay {
          position: fixed;
          top: 10%;
          left: 50%;
          transform: translateX(-50%);
          width: 90%;
          max-width: 650px;
          max-height: 80vh;
          z-index: 1000;
          padding: 24px;
          border-radius: 24px;
          display: flex;
          flex-direction: column;
          gap: 20px;
          box-shadow: 0 30px 60px rgba(0, 0, 0, 0.7);
          backdrop-filter: blur(25px);
          background: rgba(15, 23, 42, 0.85); /* Darker, distinct background */
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .history-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .title-group {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .close-btn {
          background: rgba(255, 255, 255, 0.05);
          border: none;
          color: white;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }
        .history-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding-right: 8px;
        }
        .history-item {
          padding: 16px;
          border-radius: 16px;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .history-item:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.1);
          transform: translateY(-2px);
        }
        .item-summary {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .item-info h3 {
          font-size: 1rem;
          margin-bottom: 4px;
        }
        .item-meta {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.4);
        }
        .item-badge {
          background: rgba(255, 255, 255, 0.05);
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: var(--secondary);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .platform-tag {
          display: flex;
          align-items: center;
          gap: 4px;
          margin-left: 8px;
          padding-left: 8px;
          border-left: 1px solid rgba(255, 255, 255, 0.2);
          text-transform: capitalize;
        }
        .item-details {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          overflow: hidden;
        }
        .details-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 16px;
        }
        .detail-section h4 {
          font-size: 0.75rem;
          text-transform: uppercase;
          color: rgba(255, 255, 255, 0.3);
          margin-bottom: 8px;
        }
        .detail-section p {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.8);
          line-height: 1.4;
        }
        .emotions-container {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 8px;
        }
        .emotion-tag {
          background: rgba(99, 102, 241, 0.15);
          color: #a5b4fc;
          border: 1px solid rgba(99, 102, 241, 0.3);
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .storyboard-section {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        .storyboard-section h4 {
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 12px;
        }
        .storyboard-scroller {
          display: flex;
          gap: 12px;
          overflow-x: auto;
          padding-bottom: 12px;
        }
        .storyboard-scroller::-webkit-scrollbar {
          height: 6px;
        }
        .storyboard-scroller::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 6px;
        }
        .storyboard-scene {
          min-width: 220px;
          padding: 12px;
          border-radius: 12px;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .scene-header {
          display: flex;
          justify-content: space-between;
          font-size: 0.7rem;
          color: rgba(255, 255, 255, 0.4);
          margin-bottom: 8px;
        }
        .scene-idx { font-weight: bold; color: var(--secondary); }
        .scene-voiceover {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.9);
          line-height: 1.4;
          font-style: italic;
        }
        .view-video-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-top: 12px;
          padding: 8px 16px;
          background: rgba(99, 102, 241, 0.2);
          color: white;
          border: 1px solid rgba(99, 102, 241, 0.4);
          border-radius: 8px;
          font-size: 0.8rem;
          text-decoration: none;
          transition: var(--transition);
        }
        .view-video-btn:hover {
          background: rgba(99, 102, 241, 0.4);
        }
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 0;
          color: rgba(255, 255, 255, 0.2);
          gap: 16px;
        }
        .history-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: white;
          gap: 16px;
        }
      `}</style>
    </motion.div>
  );
};

export default HistoryStep;

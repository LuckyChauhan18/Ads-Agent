import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, Send, Check, X, Plug, Unplug, ExternalLink,
  Clock, AlertCircle
} from 'lucide-react';
import { publishService, workflowService } from '../services/api';

const PLATFORM_ICONS = {
  meta: '📘',
  youtube: '📺',
  tiktok: '🎵',
  linkedin: '💼',
};

function PublishCenter({ user }) {
  const [platforms, setPlatforms] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [publishing, setPublishing] = useState(false);
  const [publishResults, setPublishResults] = useState(null);
  const [publishHistory, setPublishHistory] = useState([]);
  const [connectingPlatform, setConnectingPlatform] = useState(null);
  const [connectForm, setConnectForm] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [platformsRes, campaignsRes] = await Promise.all([
        publishService.getConnectedPlatforms(),
        workflowService.runGetDashboard(),
      ]);
      setPlatforms(platformsRes.data.platforms || []);
      setCampaigns(campaignsRes.data.campaigns || []);
    } catch (e) {
      console.error('Failed to load publish data:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (platform) => {
    try {
      await publishService.connectPlatform(platform, {
        ...connectForm,
        account_name: connectForm.account_name || user,
      });
      setConnectingPlatform(null);
      setConnectForm({});
      await loadData();
    } catch (e) {
      console.error('Connect failed:', e);
    }
  };

  const handleDisconnect = async (platform) => {
    try {
      await publishService.disconnectPlatform(platform);
      await loadData();
    } catch (e) {
      console.error('Disconnect failed:', e);
    }
  };

  const handlePublish = async () => {
    if (!selectedCampaign || selectedPlatforms.length === 0) return;
    setPublishing(true);
    setPublishResults(null);
    try {
      const res = await publishService.publishAd(
        selectedCampaign._id,
        selectedPlatforms,
        {}
      );
      setPublishResults(res.data.results);
      // Load history for this campaign
      const histRes = await publishService.getPublishHistory(selectedCampaign._id);
      setPublishHistory(histRes.data.history || []);
    } catch (e) {
      console.error('Publish failed:', e);
      setPublishResults([{ status: 'error', message: e.response?.data?.detail || 'Publish failed' }]);
    } finally {
      setPublishing(false);
    }
  };

  const loadCampaignHistory = async (campaign) => {
    setSelectedCampaign(campaign);
    setPublishResults(null);
    try {
      const res = await publishService.getPublishHistory(campaign._id);
      setPublishHistory(res.data.history || []);
    } catch (e) {
      setPublishHistory([]);
    }
  };

  const togglePlatform = (p) => {
    setSelectedPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  if (loading) return <div className="loading-state">Loading publish center...</div>;

  const connectedPlatforms = platforms.filter((p) => p.connected);

  return (
    <div className="publish-container">
      <header className="publish-header">
        <Link to="/dashboard" className="back-btn"><ArrowLeft size={18} /> Back</Link>
        <h1>Publish to Social Media</h1>
      </header>

      {/* Platform Connections */}
      <section className="platforms-section">
        <h3>Connected Platforms</h3>
        <div className="platforms-grid">
          {platforms.map((p) => (
            <div key={p.platform} className={`platform-card ${p.connected ? 'connected' : ''}`}>
              <div className="platform-top">
                <span className="platform-icon">{PLATFORM_ICONS[p.platform] || '🌐'}</span>
                <div className="platform-info">
                  <strong>{p.name}</strong>
                  {p.connected && <span className="connected-badge"><Check size={10} /> Connected</span>}
                </div>
              </div>
              {p.connected ? (
                <button className="disconnect-btn" onClick={() => handleDisconnect(p.platform)}>
                  <Unplug size={14} /> Disconnect
                </button>
              ) : (
                <>
                  {connectingPlatform === p.platform ? (
                    <div className="connect-form">
                      <input
                        placeholder="Account Name"
                        value={connectForm.account_name || ''}
                        onChange={(e) => setConnectForm({ ...connectForm, account_name: e.target.value })}
                      />
                      <input
                        placeholder="Access Token"
                        value={connectForm.access_token || ''}
                        onChange={(e) => setConnectForm({ ...connectForm, access_token: e.target.value })}
                      />
                      <div className="form-actions">
                        <button className="connect-confirm-btn" onClick={() => handleConnect(p.platform)}>
                          <Check size={14} /> Connect
                        </button>
                        <button className="cancel-btn" onClick={() => { setConnectingPlatform(null); setConnectForm({}); }}>
                          <X size={14} />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button className="connect-btn" onClick={() => setConnectingPlatform(p.platform)}>
                      <Plug size={14} /> Connect
                    </button>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Publish Section */}
      <div className="publish-content">
        <div className="campaign-select-panel">
          <h3>Select Campaign</h3>
          {campaigns.map((c) => (
            <div
              key={c._id}
              className={`campaign-select-row ${selectedCampaign?._id === c._id ? 'selected' : ''}`}
              onClick={() => loadCampaignHistory(c)}
            >
              <strong>{c.brand_name || 'Campaign'}</strong>
              <span>{c.product_name || ''}</span>
            </div>
          ))}
          {campaigns.length === 0 && <p className="empty-msg">No campaigns to publish.</p>}
        </div>

        <div className="publish-action-panel">
          {selectedCampaign ? (
            <>
              <h3>Push "{selectedCampaign.brand_name}" to:</h3>
              <div className="target-platforms">
                {connectedPlatforms.length > 0 ? (
                  connectedPlatforms.map((p) => (
                    <motion.button
                      key={p.platform}
                      className={`target-btn ${selectedPlatforms.includes(p.platform) ? 'active' : ''}`}
                      onClick={() => togglePlatform(p.platform)}
                      whileTap={{ scale: 0.95 }}
                    >
                      {PLATFORM_ICONS[p.platform]} {p.name}
                      {selectedPlatforms.includes(p.platform) && <Check size={14} />}
                    </motion.button>
                  ))
                ) : (
                  <p className="empty-msg"><AlertCircle size={14} /> Connect a platform first to publish ads.</p>
                )}
              </div>

              {selectedPlatforms.length > 0 && (
                <motion.button
                  className="publish-btn"
                  onClick={handlePublish}
                  disabled={publishing}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Send size={18} />
                  {publishing ? 'Publishing...' : `Publish to ${selectedPlatforms.length} Platform${selectedPlatforms.length > 1 ? 's' : ''}`}
                </motion.button>
              )}

              {/* Results */}
              <AnimatePresence>
                {publishResults && (
                  <motion.div
                    className="publish-results"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                  >
                    {publishResults.map((r, i) => (
                      <div key={i} className={`result-item ${r.status}`}>
                        <span>{PLATFORM_ICONS[r.platform]} {r.platform}</span>
                        <span className={`status-badge ${r.status}`}>{r.status}</span>
                        {r.external_url && (
                          <a href={r.external_url} target="_blank" rel="noreferrer" className="ext-link">
                            <ExternalLink size={12} /> View
                          </a>
                        )}
                        {r.message && <p className="result-msg">{r.message}</p>}
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Publish History */}
              {publishHistory.length > 0 && (
                <div className="publish-history">
                  <h4><Clock size={14} /> Publish History</h4>
                  {publishHistory.map((h, i) => (
                    <div key={i} className="history-row">
                      <span>{PLATFORM_ICONS[h.platform]} {h.platform}</span>
                      <span className={`status-badge ${h.status}`}>{h.status}</span>
                      <span className="history-date">{new Date(h.created_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="empty-detail">
              <Send size={48} opacity={0.15} />
              <p>Select a campaign to publish</p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .publish-container {
          width: 100%;
          max-width: 1400px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 24px;
          padding: 24px 40px 40px;
          flex: 1;
          min-height: 0;
        }
        .publish-header {
          display: flex;
          align-items: center;
          gap: 20px;
        }
        .publish-header h1 { flex: 1; font-size: 1.4rem; margin: 0; }

        .platforms-section h3 {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.5;
          margin: 0 0 12px;
        }
        .platforms-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
        }
        .platform-card {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 14px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .platform-card.connected { border-color: rgba(16, 185, 129, 0.3); }
        .platform-top { display: flex; align-items: center; gap: 10px; }
        .platform-icon { font-size: 1.5rem; }
        .platform-info { display: flex; flex-direction: column; }
        .platform-info strong { font-size: 0.85rem; }
        .connected-badge {
          font-size: 0.6rem;
          color: #34d399;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .connect-btn, .disconnect-btn {
          padding: 8px 12px;
          border-radius: 8px;
          border: none;
          font-size: 0.75rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          justify-content: center;
        }
        .connect-btn {
          background: rgba(99, 102, 241, 0.15);
          color: #818cf8;
        }
        .connect-btn:hover { background: rgba(99, 102, 241, 0.25); }
        .disconnect-btn {
          background: rgba(239, 68, 68, 0.1);
          color: #fca5a5;
        }
        .disconnect-btn:hover { background: rgba(239, 68, 68, 0.2); }

        .connect-form {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .connect-form input {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          padding: 8px 10px;
          color: white;
          font-size: 0.75rem;
          outline: none;
        }
        .connect-form input:focus { border-color: #6366f1; }
        .form-actions { display: flex; gap: 6px; }
        .connect-confirm-btn {
          flex: 1;
          background: #6366f1;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 4px;
          justify-content: center;
          font-size: 0.75rem;
        }
        .cancel-btn {
          background: rgba(255,255,255,0.1);
          color: white;
          border: none;
          border-radius: 8px;
          padding: 8px;
          cursor: pointer;
        }

        .publish-content {
          display: grid;
          grid-template-columns: 300px 1fr;
          gap: 20px;
          flex: 1;
          min-height: 0;
        }

        .campaign-select-panel {
          background: rgba(255,255,255,0.02);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 16px;
          padding: 16px;
          overflow-y: auto;
        }
        .campaign-select-panel h3 {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.5;
          margin: 0 0 12px;
        }
        .campaign-select-row {
          padding: 10px 12px;
          border-radius: 8px;
          cursor: pointer;
          margin-bottom: 4px;
          display: flex;
          flex-direction: column;
          gap: 2px;
          border: 1px solid transparent;
        }
        .campaign-select-row:hover { background: rgba(255,255,255,0.04); }
        .campaign-select-row.selected {
          background: rgba(99, 102, 241, 0.1);
          border-color: rgba(99, 102, 241, 0.3);
        }
        .campaign-select-row strong { font-size: 0.85rem; }
        .campaign-select-row span { font-size: 0.7rem; opacity: 0.5; }

        .publish-action-panel {
          background: rgba(255,255,255,0.02);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 16px;
          padding: 24px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .publish-action-panel h3 { margin: 0; font-size: 1rem; }

        .target-platforms { display: flex; flex-wrap: wrap; gap: 8px; }
        .target-btn {
          padding: 10px 16px;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(255,255,255,0.03);
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.85rem;
          transition: all 0.2s;
        }
        .target-btn.active {
          background: rgba(99, 102, 241, 0.15);
          border-color: #6366f1;
          color: #a5b4fc;
        }

        .publish-btn {
          background: linear-gradient(135deg, #6366f1, #4338ca);
          color: white;
          border: none;
          padding: 14px 24px;
          border-radius: 14px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          box-shadow: 0 8px 24px rgba(99, 102, 241, 0.25);
        }
        .publish-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .publish-results {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .result-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: 10px;
          background: rgba(255,255,255,0.03);
          flex-wrap: wrap;
        }
        .status-badge {
          padding: 2px 8px;
          border-radius: 6px;
          font-size: 0.65rem;
          font-weight: 700;
          text-transform: uppercase;
        }
        .status-badge.published { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        .status-badge.error { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }
        .ext-link {
          color: #818cf8;
          font-size: 0.75rem;
          display: flex;
          align-items: center;
          gap: 4px;
          text-decoration: none;
        }
        .result-msg { font-size: 0.75rem; opacity: 0.6; width: 100%; margin: 4px 0 0; }

        .publish-history h4 {
          font-size: 0.8rem;
          display: flex;
          align-items: center;
          gap: 6px;
          opacity: 0.5;
          margin: 0 0 10px;
        }
        .history-row {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 12px;
          border-radius: 8px;
          background: rgba(255,255,255,0.02);
          margin-bottom: 4px;
          font-size: 0.8rem;
        }
        .history-date { font-size: 0.7rem; opacity: 0.4; margin-left: auto; }

        .empty-detail {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          gap: 12px;
          opacity: 0.4;
        }
        .empty-msg {
          opacity: 0.4;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.85rem;
        }

        .back-btn {
          background: transparent;
          border: 1px solid rgba(255,255,255,0.1);
          color: white;
          padding: 8px 15px;
          border-radius: 20px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.85rem;
          cursor: pointer;
          text-decoration: none;
        }
        .back-btn:hover { background: rgba(255,255,255,0.05); }

        @media (max-width: 1024px) {
          .platforms-grid { grid-template-columns: repeat(2, 1fr); }
          .publish-content { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

export default PublishCenter;

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
        <div className="publish-title-group">
          <h1>Publish to Social Media</h1>
          <span className="publish-subtitle">Connect platforms & distribute your ads</span>
        </div>
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
          padding: 20px 24px;
          border-radius: 16px;
          background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
          border: 1px solid rgba(99,102,241,0.3);
          box-shadow: 0 8px 32px rgba(99,102,241,0.15);
        }
        .publish-header h1 {
          flex: 1;
          font-size: 1.4rem;
          margin: 0;
          background: linear-gradient(to right, #e0e7ff, #c4b5fd);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .publish-title-group {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .publish-subtitle {
          font-size: 0.75rem;
          color: rgba(165,180,252,0.6);
          letter-spacing: 0.5px;
        }

        .platforms-section h3 {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          margin: 0 0 14px;
          background: linear-gradient(135deg, #818cf8, #c084fc);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .platforms-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
        }
        .platform-card {
          background: linear-gradient(145deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 14px;
          padding: 18px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
          position: relative;
          overflow: hidden;
        }
        .platform-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #6366f1, #8b5cf6, transparent);
          opacity: 0.5;
        }
        .platform-card:hover {
          transform: translateY(-4px);
          border-color: rgba(99,102,241,0.3);
          box-shadow: 0 12px 32px rgba(0,0,0,0.3);
        }
        .platform-card.connected {
          border-color: rgba(16, 185, 129, 0.5);
          background: linear-gradient(145deg, rgba(16, 185, 129, 0.12) 0%, rgba(16, 185, 129, 0.04) 100%);
          box-shadow: 0 6px 24px rgba(16, 185, 129, 0.15);
        }
        .platform-card.connected::before {
          background: linear-gradient(90deg, #10b981, #34d399, transparent);
          opacity: 1;
        }
        .platform-top { display: flex; align-items: center; gap: 10px; }
        .platform-icon { font-size: 1.8rem; }
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
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.15));
          border: 1px solid rgba(99, 102, 241, 0.3);
          color: #c7d2fe;
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
        }
        .connect-btn:hover {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(168, 85, 247, 0.25));
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
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
          background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(99,102,241,0.2);
          border-radius: 16px;
          padding: 16px;
          overflow-y: auto;
          box-shadow: 0 8px 32px rgba(0,0,0,0.2);
          position: relative;
        }
        .campaign-select-panel::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
          border-radius: 16px 16px 0 0;
        }
        .campaign-select-panel h3 {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          background: linear-gradient(135deg, #818cf8, #c084fc);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin: 8px 0 14px;
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
          transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
          position: relative;
        }
        .campaign-select-row::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background: linear-gradient(180deg, #6366f1, #8b5cf6, #ec4899);
          opacity: 0;
          transition: opacity 0.3s;
          border-radius: 8px 0 0 8px;
        }
        .campaign-select-row:hover {
          background: rgba(255,255,255,0.06);
          transform: translateX(4px);
        }
        .campaign-select-row:hover::before {
          opacity: 1;
        }
        .campaign-select-row.selected {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.1));
          border-color: rgba(99, 102, 241, 0.4);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
        }
        .campaign-select-row.selected::before {
          opacity: 1;
        }
        .campaign-select-row strong { font-size: 0.85rem; }
        .campaign-select-row span { font-size: 0.7rem; opacity: 0.5; }

        .publish-action-panel {
          background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(99,102,241,0.15);
          border-radius: 16px;
          padding: 24px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.2);
          position: relative;
        }
        .publish-action-panel::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #ec4899, #8b5cf6, #6366f1);
          border-radius: 16px 16px 0 0;
        }
        .publish-action-panel h3 {
          margin: 8px 0 0;
          font-size: 1rem;
        }

        .target-platforms { display: flex; flex-wrap: wrap; gap: 8px; }
        .target-btn {
          padding: 10px 16px;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(255,255,255,0.04);
          backdrop-filter: blur(8px);
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.85rem;
          transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
        }
        .target-btn:hover {
          background: rgba(255,255,255,0.08);
          border-color: rgba(99, 102, 241, 0.3);
          transform: translateY(-1px);
        }
        .target-btn.active {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.15));
          border-color: rgba(99, 102, 241, 0.5);
          color: #c7d2fe;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
        }

        .publish-btn {
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 30%, #ec4899 70%, #f43f5e 100%);
          color: white;
          border: none;
          padding: 16px 28px;
          border-radius: 14px;
          font-size: 1rem;
          font-weight: 700;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4), 0 0 60px rgba(236,72,153,0.15);
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
          position: relative;
          overflow: hidden;
          letter-spacing: 0.3px;
        }
        .publish-btn::before {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(135deg, transparent, rgba(255,255,255,0.2));
          opacity: 0;
          transition: opacity 0.3s;
        }
        .publish-btn:hover::before {
          opacity: 1;
        }
        .publish-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

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
          background: rgba(255,255,255,0.04);
          backdrop-filter: blur(8px);
          border: 1px solid rgba(255,255,255,0.08);
          flex-wrap: wrap;
          transition: all 0.2s ease;
        }
        .result-item:hover {
          background: rgba(255,255,255,0.06);
          border-color: rgba(255,255,255,0.12);
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
          background: rgba(255,255,255,0.03);
          backdrop-filter: blur(8px);
          border: 1px solid rgba(255,255,255,0.05);
          margin-bottom: 4px;
          font-size: 0.8rem;
          transition: all 0.2s ease;
        }
        .history-row:hover {
          background: rgba(255,255,255,0.05);
          border-color: rgba(255,255,255,0.1);
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
          background: rgba(255,255,255,0.08);
          border: 1px solid rgba(255,255,255,0.15);
          color: white;
          padding: 8px 16px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.85rem;
          cursor: pointer;
          text-decoration: none;
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
        }
        .back-btn:hover {
          background: rgba(255,255,255,0.15);
          transform: translateX(-2px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }

        @media (max-width: 1024px) {
          .platforms-grid { grid-template-columns: repeat(2, 1fr); }
          .publish-content { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

export default PublishCenter;

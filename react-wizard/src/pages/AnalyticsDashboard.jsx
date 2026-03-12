import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  BarChart3, Eye, Heart, MessageCircle, Share2, MousePointerClick,
  TrendingUp, ArrowLeft, RefreshCw, Zap, Target
} from 'lucide-react';
import { analyticsService, workflowService } from '../services/api';

function AnalyticsDashboard({ user }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [campaignMetrics, setCampaignMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [analyticsRes, campaignsRes] = await Promise.all([
        analyticsService.getDashboardAnalytics(),
        workflowService.runGetDashboard(),
      ]);
      setDashboardData(analyticsRes.data);
      setCampaigns(campaignsRes.data.campaigns || []);
    } catch (e) {
      console.error('Failed to load analytics:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadCampaignMetrics = async (campaignId) => {
    try {
      const res = await analyticsService.getCampaignAnalytics(campaignId);
      setCampaignMetrics(res.data);
    } catch (e) {
      console.error('Failed to load campaign metrics:', e);
    }
  };

  const handleSeedDemo = async (campaignId) => {
    setSeeding(true);
    try {
      await analyticsService.trackEvent(campaignId, 'view', {});
      await analyticsService.seedDemoData(campaignId);
      await loadDashboard();
      if (selectedCampaign?._id === campaignId) {
        await loadCampaignMetrics(campaignId);
      }
    } catch (e) {
      console.error('Seed failed:', e);
    } finally {
      setSeeding(false);
    }
  };

  const selectCampaign = (campaign) => {
    setSelectedCampaign(campaign);
    loadCampaignMetrics(campaign._id);
  };

  if (loading) return <div className="loading-state">Loading analytics...</div>;

  const totals = dashboardData?.total || {};

  return (
    <div className="analytics-container">
      <header className="analytics-header">
        <Link to="/dashboard" className="back-btn"><ArrowLeft size={18} /> Back</Link>
        <div className="analytics-title-group">
          <h1>Ad Performance Analytics</h1>
          <span className="analytics-subtitle">Real-time campaign insights & metrics</span>
        </div>
        <button className="refresh-btn" onClick={loadDashboard}><RefreshCw size={16} /> Refresh</button>
      </header>

      {/* Overview Metrics Cards */}
      <div className="metrics-overview">
        <MetricCard icon={<Eye />} label="Total Views" value={formatNumber(totals.views)} color="#818cf8" />
        <MetricCard icon={<Heart />} label="Total Likes" value={formatNumber(totals.likes)} color="#f472b6" />
        <MetricCard icon={<MessageCircle />} label="Comments" value={formatNumber(totals.comments)} color="#34d399" />
        <MetricCard icon={<Share2 />} label="Shares" value={formatNumber(totals.shares)} color="#60a5fa" />
        <MetricCard icon={<MousePointerClick />} label="Clicks" value={formatNumber(totals.clicks)} color="#fbbf24" />
        <MetricCard icon={<Target />} label="Impressions" value={formatNumber(totals.impressions)} color="#a78bfa" />
        <MetricCard icon={<Zap />} label="CTR" value={`${totals.ctr || 0}%`} color="#fb923c" />
        <MetricCard icon={<TrendingUp />} label="Engagement" value={`${totals.engagement_rate || 0}%`} color="#4ade80" />
      </div>

      {/* Campaign List */}
      <div className="analytics-content">
        <div className="campaigns-list-panel">
          <h3>Campaigns ({campaigns.length})</h3>
          {campaigns.length === 0 && <p className="empty-msg">No campaigns yet. Create one first.</p>}
          {campaigns.map((c) => (
            <motion.div
              key={c._id}
              className={`campaign-row ${selectedCampaign?._id === c._id ? 'selected' : ''}`}
              onClick={() => selectCampaign(c)}
              whileHover={{ x: 4 }}
            >
              <div className="campaign-row-info">
                <strong>{c.brand_name || 'Campaign'}</strong>
                <span>{c.product_name || ''}</span>
              </div>
              <div className="campaign-row-meta">
                <span className="platform-badge">{c.platform || 'N/A'}</span>
                <button
                  className="seed-btn"
                  onClick={(e) => { e.stopPropagation(); handleSeedDemo(c._id); }}
                  disabled={seeding}
                  title="Generate demo analytics"
                >
                  <BarChart3 size={12} />
                </button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Campaign Detail Metrics */}
        <div className="campaign-detail-panel">
          {selectedCampaign && campaignMetrics ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <h3>{selectedCampaign.brand_name}: {selectedCampaign.product_name}</h3>
              <div className="detail-metrics-grid">
                <DetailMetric label="Views" value={campaignMetrics.metrics?.views || 0} icon={<Eye size={16} />} />
                <DetailMetric label="Likes" value={campaignMetrics.metrics?.likes || 0} icon={<Heart size={16} />} />
                <DetailMetric label="Comments" value={campaignMetrics.metrics?.comments || 0} icon={<MessageCircle size={16} />} />
                <DetailMetric label="Shares" value={campaignMetrics.metrics?.shares || 0} icon={<Share2 size={16} />} />
                <DetailMetric label="Clicks" value={campaignMetrics.metrics?.clicks || 0} icon={<MousePointerClick size={16} />} />
                <DetailMetric label="Impressions" value={campaignMetrics.metrics?.impressions || 0} icon={<Target size={16} />} />
                <DetailMetric label="CTR" value={`${campaignMetrics.metrics?.ctr || 0}%`} icon={<Zap size={16} />} highlight />
                <DetailMetric label="Engagement" value={`${campaignMetrics.metrics?.engagement_rate || 0}%`} icon={<TrendingUp size={16} />} highlight />
              </div>

              {/* Simple Bar Visualization */}
              <div className="bar-chart-section">
                <h4>Performance Breakdown</h4>
                <div className="bar-chart">
                  {['views', 'likes', 'comments', 'shares', 'clicks'].map((key) => {
                    const val = campaignMetrics.metrics?.[key] || 0;
                    const maxVal = Math.max(
                      ...[campaignMetrics.metrics?.views || 1, campaignMetrics.metrics?.impressions || 1]
                    );
                    const pct = Math.min((val / maxVal) * 100, 100);
                    return (
                      <div key={key} className="bar-row">
                        <span className="bar-label">{key}</span>
                        <div className="bar-track">
                          <motion.div
                            className="bar-fill"
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut' }}
                          />
                        </div>
                        <span className="bar-value">{formatNumber(val)}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="empty-detail">
              <BarChart3 size={48} opacity={0.2} />
              <p>Select a campaign to view its analytics</p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .analytics-container {
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
        .analytics-header {
          display: flex;
          align-items: center;
          gap: 20px;
          padding: 20px 24px;
          border-radius: 16px;
          background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3b0764 100%);
          border: 1px solid rgba(99,102,241,0.3);
          box-shadow: 0 8px 32px rgba(99,102,241,0.15);
        }
        .analytics-header h1 {
          flex: 1;
          font-size: 1.4rem;
          margin: 0;
          background: linear-gradient(to right, #e0e7ff, #c4b5fd);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .analytics-title-group {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .analytics-subtitle {
          font-size: 0.75rem;
          color: rgba(165,180,252,0.6);
          letter-spacing: 0.5px;
        }
        .refresh-btn {
          background: rgba(255,255,255,0.08);
          border: 1px solid rgba(255,255,255,0.15);
          color: white;
          padding: 8px 18px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          gap: 6px;
          cursor: pointer;
          font-size: 0.8rem;
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
        }
        .refresh-btn:hover {
          background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.2));
          border-color: rgba(99,102,241,0.5);
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(99,102,241,0.3);
        }

        .metrics-overview {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
        }

        .metric-card {
          background: linear-gradient(145deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 16px;
          padding: 18px;
          display: flex;
          align-items: center;
          gap: 14px;
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
          position: relative;
          overflow: hidden;
        }
        .metric-card:hover {
          transform: translateY(-4px) scale(1.02);
          box-shadow: 0 12px 32px rgba(0,0,0,0.3);
          border-color: rgba(255,255,255,0.2);
        }
        .metric-icon {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
          box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .metric-card:hover .metric-icon {
          transform: scale(1.1) rotate(5deg);
        }
        .metric-info h4 {
          margin: 0;
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.5;
        }
        .metric-info p {
          margin: 4px 0 0;
          font-size: 1.3rem;
          font-weight: 700;
        }

        .analytics-content {
          display: grid;
          grid-template-columns: 320px 1fr;
          gap: 20px;
          flex: 1;
          min-height: 0;
        }

        .campaigns-list-panel {
          background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(99,102,241,0.2);
          border-radius: 16px;
          padding: 16px;
          overflow-y: auto;
          box-shadow: 0 8px 32px rgba(0,0,0,0.2);
          position: relative;
        }
        .campaigns-list-panel::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
          border-radius: 16px 16px 0 0;
        }
        .campaigns-list-panel h3 {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          background: linear-gradient(135deg, #818cf8, #c084fc);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin: 8px 0 14px;
        }

        .campaign-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          border-radius: 10px;
          cursor: pointer;
          margin-bottom: 6px;
          transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
          border: 1px solid transparent;
          position: relative;
        }
        .campaign-row::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background: linear-gradient(180deg, #6366f1, #8b5cf6, #ec4899);
          opacity: 0;
          transition: opacity 0.3s;
          border-radius: 10px 0 0 10px;
        }
        .campaign-row:hover {
          background: rgba(255,255,255,0.06);
          transform: translateX(4px);
        }
        .campaign-row:hover::before {
          opacity: 1;
        }
        .campaign-row.selected {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.1));
          border-color: rgba(99, 102, 241, 0.4);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
        }
        .campaign-row.selected::before {
          opacity: 1;
        }
        .campaign-row-info { display: flex; flex-direction: column; gap: 2px; }
        .campaign-row-info strong { font-size: 0.85rem; }
        .campaign-row-info span { font-size: 0.7rem; opacity: 0.5; }
        .campaign-row-meta { display: flex; align-items: center; gap: 8px; }
        .platform-badge {
          font-size: 0.6rem;
          padding: 2px 8px;
          border-radius: 8px;
          background: rgba(255,255,255,0.08);
          text-transform: uppercase;
        }
        .seed-btn {
          width: 24px;
          height: 24px;
          border-radius: 6px;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.15));
          border: 1px solid rgba(99, 102, 241, 0.3);
          color: #c7d2fe;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s cubic-bezier(0.16,1,0.3,1);
        }
        .seed-btn:hover {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.35), rgba(168, 85, 247, 0.25));
          transform: scale(1.1);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .campaign-detail-panel {
          background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(99,102,241,0.15);
          border-radius: 16px;
          padding: 24px;
          overflow-y: auto;
          box-shadow: 0 8px 32px rgba(0,0,0,0.2);
          position: relative;
        }
        .campaign-detail-panel::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #ec4899, #8b5cf6, #6366f1);
          border-radius: 16px 16px 0 0;
        }
        .campaign-detail-panel h3 {
          margin: 8px 0 20px;
          font-size: 1.1rem;
          background: linear-gradient(135deg, #e0e7ff, #f9a8d4);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .detail-metrics-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 10px;
          margin-bottom: 24px;
        }

        .detail-metric {
          background: linear-gradient(145deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px;
          padding: 16px;
          text-align: center;
          transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
        }
        .detail-metric:hover {
          transform: translateY(-3px);
          border-color: rgba(99,102,241,0.3);
          box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }
        .detail-metric.highlight {
          background: linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(168,85,247,0.12) 100%);
          border-color: rgba(99,102,241,0.4);
          box-shadow: 0 6px 20px rgba(99,102,241,0.2);
        }
        .detail-metric .dm-icon { opacity: 0.4; margin-bottom: 6px; }
        .detail-metric .dm-value { font-size: 1.2rem; font-weight: 700; margin: 0; }
        .detail-metric .dm-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.4; margin: 4px 0 0; }

        .bar-chart-section h4 {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          margin: 0 0 14px;
          background: linear-gradient(135deg, #818cf8, #ec4899);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .bar-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 10px;
        }
        .bar-label {
          width: 70px;
          font-size: 0.75rem;
          text-transform: capitalize;
          opacity: 0.6;
        }
        .bar-track {
          flex: 1;
          height: 8px;
          background: rgba(255,255,255,0.05);
          border-radius: 4px;
          overflow: hidden;
        }
        .bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #6366f1 0%, #a855f7 40%, #ec4899 70%, #f43f5e 100%);
          border-radius: 4px;
          box-shadow: 0 0 16px rgba(99,102,241,0.5), 0 0 4px rgba(236,72,153,0.3);
        }
        .bar-value {
          width: 60px;
          text-align: right;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .empty-detail {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          gap: 12px;
          opacity: 0.4;
        }
        .empty-msg { opacity: 0.4; text-align: center; margin-top: 40px; }

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
          .metrics-overview { grid-template-columns: repeat(2, 1fr); }
          .analytics-content { grid-template-columns: 1fr; }
          .detail-metrics-grid { grid-template-columns: repeat(2, 1fr); }
        }
      `}</style>
    </div>
  );
}

function MetricCard({ icon, label, value, color }) {
  return (
    <motion.div className="metric-card" whileHover={{ scale: 1.02 }} style={{ borderLeft: `4px solid ${color}`, background: `linear-gradient(135deg, ${color}12, ${color}06)` }}>
      <div className="metric-icon" style={{ background: `${color}25`, color }}>
        {icon}
      </div>
      <div className="metric-info">
        <h4>{label}</h4>
        <p style={{ color }}>{value}</p>
      </div>
    </motion.div>
  );
}

function DetailMetric({ label, value, icon, highlight }) {
  return (
    <div className={`detail-metric ${highlight ? 'highlight' : ''}`}>
      <div className="dm-icon">{icon}</div>
      <p className="dm-value">{typeof value === 'number' ? formatNumber(value) : value}</p>
      <p className="dm-label">{label}</p>
    </div>
  );
}

function formatNumber(num) {
  if (!num && num !== 0) return '0';
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

export default AnalyticsDashboard;

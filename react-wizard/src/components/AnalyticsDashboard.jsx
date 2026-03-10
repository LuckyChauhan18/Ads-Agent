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
      // Seed with random data via the seed endpoint
      const res = await fetch(`http://localhost:8000/analytics/seed/${campaignId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('spectra_token')}`,
        },
      });
      if (res.ok) {
        await loadDashboard();
        if (selectedCampaign?._id === campaignId) {
          await loadCampaignMetrics(campaignId);
        }
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
        <h1>Ad Performance Analytics</h1>
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
        }
        .analytics-header h1 {
          flex: 1;
          font-size: 1.4rem;
          margin: 0;
        }
        .refresh-btn {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: white;
          padding: 8px 16px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          gap: 6px;
          cursor: pointer;
          font-size: 0.8rem;
        }
        .refresh-btn:hover { background: rgba(255,255,255,0.1); }

        .metrics-overview {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
        }

        .metric-card {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 16px;
          padding: 16px;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .metric-icon {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
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
          background: rgba(255,255,255,0.02);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 16px;
          padding: 16px;
          overflow-y: auto;
        }
        .campaigns-list-panel h3 {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.5;
          margin: 0 0 12px;
        }

        .campaign-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          border-radius: 10px;
          cursor: pointer;
          margin-bottom: 6px;
          transition: all 0.2s;
          border: 1px solid transparent;
        }
        .campaign-row:hover { background: rgba(255,255,255,0.04); }
        .campaign-row.selected {
          background: rgba(99, 102, 241, 0.1);
          border-color: rgba(99, 102, 241, 0.3);
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
          background: rgba(99, 102, 241, 0.15);
          border: none;
          color: #818cf8;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .seed-btn:hover { background: rgba(99, 102, 241, 0.3); }

        .campaign-detail-panel {
          background: rgba(255,255,255,0.02);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 16px;
          padding: 24px;
          overflow-y: auto;
        }
        .campaign-detail-panel h3 {
          margin: 0 0 20px;
          font-size: 1.1rem;
        }

        .detail-metrics-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 10px;
          margin-bottom: 24px;
        }

        .detail-metric {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          padding: 14px;
          text-align: center;
        }
        .detail-metric.highlight {
          background: rgba(99, 102, 241, 0.08);
          border-color: rgba(99, 102, 241, 0.2);
        }
        .detail-metric .dm-icon { opacity: 0.4; margin-bottom: 6px; }
        .detail-metric .dm-value { font-size: 1.2rem; font-weight: 700; margin: 0; }
        .detail-metric .dm-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.4; margin: 4px 0 0; }

        .bar-chart-section h4 {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.5;
          margin: 0 0 14px;
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
          background: linear-gradient(90deg, #6366f1, #818cf8);
          border-radius: 4px;
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
    <motion.div className="metric-card" whileHover={{ scale: 1.02 }}>
      <div className="metric-icon" style={{ background: `${color}20`, color }}>
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

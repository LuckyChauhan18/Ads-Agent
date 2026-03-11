import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Layout as LayoutIcon, Image as ImageIcon, FileText, User, ArrowLeft,
  ExternalLink, Calendar, Sparkles, Video, Layers, Plus, TrendingUp,
  Clock, Zap, ChevronRight, FolderOpen, ImagePlus, UserCircle
} from 'lucide-react';
import { workflowService } from '../services/api';

function Dashboard({ user }) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [activeTab, setActiveTab] = React.useState('campaigns');
  const [selectedCampaign, setSelectedCampaign] = React.useState(null);
  const navigate = useNavigate();

  React.useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const res = await workflowService.runGetDashboard();
      setData(res.data);
    } catch (e) {
      console.error("Dashboard fetch failed", e);
    } finally {
      setLoading(false);
    }
  };

  const campaignCount = data?.campaigns?.length || 0;
  const logoCount = data?.assets?.logos?.length || 0;
  const productCount = data?.assets?.products?.length || 0;
  const avatarCount = data?.assets?.avatars?.length || 0;

  const tabs = [
    { key: 'campaigns', label: 'Campaigns', icon: Layers, count: campaignCount },
    { key: 'logos', label: 'Logos', icon: ImageIcon, count: logoCount },
    { key: 'products', label: 'Products', icon: FolderOpen, count: productCount },
    { key: 'avatars', label: 'Avatars', icon: UserCircle, count: avatarCount },
  ];

  const stats = [
    { label: 'Total Campaigns', value: campaignCount, icon: Layers, color: '#6366f1', bg: 'rgba(99,102,241,0.12)' },
    { label: 'Assets Uploaded', value: logoCount + productCount + avatarCount, icon: ImagePlus, color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
    { label: 'AI Avatars', value: avatarCount, icon: UserCircle, color: '#f472b6', bg: 'rgba(244,114,182,0.12)' },
    { label: 'Videos Created', value: data?.campaigns?.filter(c => c.video_url)?.length || 0, icon: Video, color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  ];

  if (loading) return (
    <div className="db-loading">
      <div className="db-loading-spinner" />
      <p>Loading your creative hub...</p>
    </div>
  );

  return (
    <div className="db-root">
      {/* Welcome Hero */}
      <motion.section
        className="db-hero"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="db-hero-left">
          <div className="db-hero-avatar">
            {user?.[0]?.toUpperCase() || 'U'}
          </div>
          <div>
            <h1 className="db-hero-title">Welcome back, <span className="db-hero-name">{data?.user_info?.full_name || user}</span></h1>
            <p className="db-hero-sub">Here's an overview of your creative workspace</p>
          </div>
        </div>
        <button className="db-create-btn" onClick={() => navigate('/create')}>
          <Plus size={18} />
          New Campaign
        </button>
      </motion.section>

      {/* Stats Row */}
      <motion.section
        className="db-stats-row"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        {stats.map((s, i) => {
          const Icon = s.icon;
          return (
            <div className="db-stat-card" key={i}>
              <div className="db-stat-icon" style={{ background: s.bg, color: s.color }}>
                <Icon size={20} />
              </div>
              <div className="db-stat-text">
                <span className="db-stat-value">{s.value}</span>
                <span className="db-stat-label">{s.label}</span>
              </div>
            </div>
          );
        })}
      </motion.section>

      {/* Tab Navigation */}
      <motion.nav
        className="db-tabs"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.15 }}
      >
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              className={`db-tab ${activeTab === tab.key ? 'db-tab-active' : ''}`}
              onClick={() => { setActiveTab(tab.key); setSelectedCampaign(null); }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
              <span className="db-tab-count">{tab.count}</span>
            </button>
          );
        })}
      </motion.nav>

      {/* Content Area */}
      <div className="db-content">
        <AnimatePresence mode="wait">
          {activeTab === 'campaigns' && (
            <motion.div key="campaigns" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="campaigns-view">
              {!selectedCampaign ? (
                campaignCount > 0 ? (
                  <div className="db-grid">
                    {data.campaigns.map((c, idx) => (
                      <motion.div
                        key={c._id}
                        className="db-card"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        onClick={() => setSelectedCampaign(c)}
                        whileHover={{ y: -6, scale: 1.015 }}
                      >
                        <div className="db-card-top">
                          <div className="db-card-brand-icon">
                            {c.brand_name?.[0]?.toUpperCase() || 'C'}
                          </div>
                          <div className="db-card-meta">
                            <h4 className="db-card-brand">{c.brand_name}</h4>
                            <span className="db-card-date">
                              <Clock size={11} />
                              {new Date(c.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                            </span>
                          </div>
                          <ChevronRight size={16} className="db-card-arrow" />
                        </div>
                        <p className="db-card-product">{c.product_name}</p>
                        <div className="db-card-bottom">
                          <span className="db-card-badge">{c.platform || 'instagram'}</span>
                          {c.funnel_stage && <span className="db-card-badge db-card-badge-green">{c.funnel_stage}</span>}
                          {c.video_url && <span className="db-card-badge db-card-badge-amber"><Video size={10} /> Video</span>}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="db-empty">
                    <div className="db-empty-icon"><Sparkles size={40} /></div>
                    <h3>No campaigns yet</h3>
                    <p>Create your first AI-powered ad campaign to get started</p>
                    <button className="db-create-btn" onClick={() => navigate('/create')}>
                      <Plus size={18} /> Create Campaign
                    </button>
                  </div>
                )
              ) : (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="db-detail"
                >
                  <div className="db-detail-header">
                    <button className="db-detail-back" onClick={() => setSelectedCampaign(null)}>
                      <ArrowLeft size={16} /> All Campaigns
                    </button>
                    <div className="db-detail-title-row">
                      <div>
                        <h2 className="db-detail-title">{selectedCampaign.brand_name}: {selectedCampaign.product_name}</h2>
                        <div className="campaign-meta-row">
                          <span className="db-detail-platform">{selectedCampaign.platform}</span>
                          {selectedCampaign.funnel_stage && <span className="meta-badge funnel">{selectedCampaign.funnel_stage}</span>}
                          {selectedCampaign.ad_length && <span className="meta-badge">{selectedCampaign.ad_length}s</span>}
                          {selectedCampaign.primary_emotions?.map((e, i) => (
                            <span key={i} className="meta-badge emotion">{e}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="db-detail-body">
                    {selectedCampaign.campaign_psychology?.product_understanding && (
                      <section className="db-section">
                        <h3 className="db-section-title">Product Overview</h3>
                        <div className="db-section-content">
                          <p className="product-desc">{selectedCampaign.campaign_psychology.product_understanding.description}</p>
                          <div className="product-chips">
                            {selectedCampaign.campaign_psychology.product_understanding.features?.map((f, i) => (
                              <span key={i} className="feature-chip">{f}</span>
                            ))}
                          </div>
                          {selectedCampaign.campaign_psychology.product_understanding.target_user && (
                            <div className="target-user">
                              <label>Target Audience</label>
                              <p>{selectedCampaign.campaign_psychology.product_understanding.target_user}</p>
                            </div>
                          )}
                        </div>
                      </section>
                    )}

                    {selectedCampaign.pattern_blueprint?.pattern_blueprint && (
                      <section className="db-section">
                        <h3 className="db-section-title">Strategy Blueprint</h3>
                        <div className="strategy-grid">
                          {[
                            { label: 'Hook', value: selectedCampaign.pattern_blueprint.pattern_blueprint.hook_type },
                            { label: 'Tone', value: selectedCampaign.pattern_blueprint.pattern_blueprint.tone },
                            { label: 'Angle', value: selectedCampaign.pattern_blueprint.pattern_blueprint.angle },
                            { label: 'CTA', value: selectedCampaign.pattern_blueprint.pattern_blueprint.cta },
                            { label: 'Text Density', value: selectedCampaign.pattern_blueprint.pattern_blueprint.text_density },
                            { label: 'Opening', value: selectedCampaign.pattern_blueprint.pattern_blueprint.opening_style },
                          ].filter(item => item.value).map((item, i) => (
                            <div key={i} className="strategy-card">
                              <label>{item.label}</label>
                              <span>{item.value}</span>
                            </div>
                          ))}
                        </div>
                        {selectedCampaign.pattern_blueprint.pattern_blueprint.scene_flow && (
                          <div className="scene-flow-row">
                            <label>Scene Flow:</label>
                            {selectedCampaign.pattern_blueprint.pattern_blueprint.scene_flow.map((s, i) => (
                              <span key={i} className="flow-step">{s}{i < selectedCampaign.pattern_blueprint.pattern_blueprint.scene_flow.length - 1 ? ' → ' : ''}</span>
                            ))}
                          </div>
                        )}
                      </section>
                    )}

                    <section className="db-section">
                      <h3 className="db-section-title">Storyboard & Script</h3>
                      <div className="storyboard-list">
                        {selectedCampaign.final_storyboard?.scenes?.map((scene, i) => (
                          <div key={i} className="scene-row">
                            <div className="scene-meta">
                              <span className="scene-num">Scene {i + 1}</span>
                              <span className="scene-intent">{scene.intent}</span>
                            </div>
                            <p className="scene-voiceover">"{scene.voiceover}"</p>
                          </div>
                        ))}
                        {!selectedCampaign.final_storyboard && <p className="info-text">Script will appear here after generation.</p>}
                      </div>
                    </section>

                    <div className="db-detail-grid-2col">
                      <section className="db-section">
                        <h3 className="db-section-title">Visual Assets</h3>
                        <div className="asset-previews">
                          {selectedCampaign.asset_id && (
                            <div className="asset-item">
                              <label>Product Images</label>
                              <span className="info-text">Linked to Asset ID: {selectedCampaign.asset_id}</span>
                            </div>
                          )}
                          {selectedCampaign.product_logo && (
                            <div className="asset-item">
                              <label>Logo</label>
                              <img src={selectedCampaign.product_logo.startsWith('http') ? selectedCampaign.product_logo : `http://localhost:8000${selectedCampaign.product_logo}`} alt="Logo" className="mini-preview" />
                            </div>
                          )}
                          {!selectedCampaign.asset_id && !selectedCampaign.product_logo && <p className="info-text">Assets will appear after rendering.</p>}
                        </div>
                      </section>

                      <section className="db-section">
                        <h3 className="db-section-title">Avatar Configuration</h3>
                        <div className="avatar-info">
                          {selectedCampaign.avatar_config ? (
                            <div className="avatar-preview-row">
                              {selectedCampaign.avatar_config.selected_avatars?.map((av, i) => (
                                <img key={i} src={av.url.startsWith('http') ? av.url : `http://localhost:8000${av.url}`} alt="Avatar" className="avatar-thumb" />
                              )) || <p className="info-text">Single avatar used.</p>}
                            </div>
                          ) : <p className="info-text">Avatar will appear after selection.</p>}
                        </div>
                      </section>
                    </div>

                    {selectedCampaign.video_url && (
                      <section className="db-section">
                        <h3 className="db-section-title">Generated Video</h3>
                        <div className="video-container">
                          <video controls src={selectedCampaign.video_url} className="final-video" />
                        </div>
                      </section>
                    )}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}

          {activeTab === 'logos' && (
            <motion.div key="logos" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {logoCount > 0 ? (
                <div className="db-asset-grid">
                  {data.assets.logos.map(l => (
                    <motion.div key={l.id} className="db-asset-card" whileHover={{ y: -4, scale: 1.02 }}>
                      <div className="db-asset-img-wrap">
                        <img src={`http://localhost:8000${l.url}`} alt="Logo" />
                      </div>
                      <p className="db-asset-name">{l.filename}</p>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="db-empty">
                  <div className="db-empty-icon"><ImageIcon size={40} /></div>
                  <h3>No logos uploaded</h3>
                  <p>Upload brand logos when creating a campaign</p>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'products' && (
            <motion.div key="products" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {productCount > 0 ? (
                <div className="db-asset-grid">
                  {data.assets.products.map(p => (
                    <motion.div key={p.id} className="db-asset-card" whileHover={{ y: -4, scale: 1.02 }}>
                      <div className="db-asset-img-wrap">
                        <img src={`http://localhost:8000${p.url}`} alt="Product" />
                      </div>
                      <p className="db-asset-name">{p.filename}</p>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="db-empty">
                  <div className="db-empty-icon"><FolderOpen size={40} /></div>
                  <h3>No product images</h3>
                  <p>Product images will appear here after upload</p>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'avatars' && (
            <motion.div key="avatars" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {avatarCount > 0 ? (
                <div className="db-asset-grid">
                  {data.assets.avatars.map(a => (
                    <motion.div key={a.id} className="db-asset-card" whileHover={{ y: -4, scale: 1.02 }}>
                      <div className="db-asset-img-wrap avatar-img-wrap">
                        <img src={`http://localhost:8000${a.url}`} alt="Avatar" />
                      </div>
                      <p className="db-asset-name">{a.filename}</p>
                      {a.created_at && (
                        <span className="db-asset-date">{new Date(a.created_at).toLocaleDateString()}</span>
                      )}
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="db-empty">
                  <div className="db-empty-icon"><UserCircle size={40} /></div>
                  <h3>No AI avatars</h3>
                  <p>Avatars will be generated during campaign creation</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style>{`
        /* ── Dashboard Root ── */
        .db-root {
          width: 100%;
          flex: 1;
          min-height: 0;
          display: flex;
          flex-direction: column;
          padding: 28px 36px 36px;
          margin: 0 auto;
          max-width: 1400px;
          gap: 24px;
        }

        /* ── Loading ── */
        .db-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          flex: 1;
          gap: 16px;
          color: rgba(255,255,255,0.5);
        }
        .db-loading-spinner {
          width: 36px;
          height: 36px;
          border: 3px solid rgba(99,102,241,0.2);
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: db-spin 0.8s linear infinite;
        }
        @keyframes db-spin { to { transform: rotate(360deg); } }

        /* ── Hero / Welcome ── */
        .db-hero {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          padding: 24px 28px;
          border-radius: 20px;
          background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.08) 100%);
          border: 1px solid rgba(99,102,241,0.15);
        }
        .db-hero-left {
          display: flex;
          align-items: center;
          gap: 18px;
        }
        .db-hero-avatar {
          width: 54px;
          height: 54px;
          border-radius: 16px;
          background: linear-gradient(135deg, #6366f1, #a855f7);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 1.4rem;
          color: white;
          box-shadow: 0 8px 24px rgba(99,102,241,0.35);
          flex-shrink: 0;
        }
        .db-hero-title {
          font-size: 1.35rem;
          margin: 0;
          font-weight: 600;
          color: rgba(255,255,255,0.9);
        }
        .db-hero-name {
          background: linear-gradient(90deg, #a5b4fc, #c4b5fd);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: 800;
        }
        .db-hero-sub {
          margin: 4px 0 0;
          font-size: 0.85rem;
          color: rgba(255,255,255,0.45);
        }

        /* ── Create Button ── */
        .db-create-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          border: none;
          border-radius: 14px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: white;
          font-weight: 700;
          font-size: 0.9rem;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
          box-shadow: 0 4px 16px rgba(99,102,241,0.35);
          white-space: nowrap;
        }
        .db-create-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 28px rgba(99,102,241,0.45);
        }

        /* ── Stats Row ── */
        .db-stats-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
        }
        .db-stat-card {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 18px 20px;
          border-radius: 16px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          transition: all 0.3s ease;
        }
        .db-stat-card:hover {
          background: rgba(255,255,255,0.05);
          border-color: rgba(255,255,255,0.1);
        }
        .db-stat-icon {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .db-stat-text {
          display: flex;
          flex-direction: column;
        }
        .db-stat-value {
          font-size: 1.5rem;
          font-weight: 800;
          color: white;
          line-height: 1;
        }
        .db-stat-label {
          font-size: 0.75rem;
          color: rgba(255,255,255,0.4);
          margin-top: 4px;
        }

        /* ── Tab Navigation ── */
        .db-tabs {
          display: flex;
          gap: 8px;
          padding: 6px;
          background: rgba(255,255,255,0.03);
          border-radius: 14px;
          border: 1px solid rgba(255,255,255,0.06);
          width: fit-content;
        }
        .db-tab {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 18px;
          border: none;
          border-radius: 10px;
          background: transparent;
          color: rgba(255,255,255,0.45);
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.25s ease;
        }
        .db-tab:hover {
          color: rgba(255,255,255,0.7);
          background: rgba(255,255,255,0.04);
        }
        .db-tab-active {
          background: rgba(99,102,241,0.15) !important;
          color: #a5b4fc !important;
          box-shadow: 0 2px 8px rgba(99,102,241,0.15);
        }
        .db-tab-count {
          font-size: 0.7rem;
          background: rgba(255,255,255,0.08);
          padding: 2px 8px;
          border-radius: 8px;
          font-weight: 700;
        }
        .db-tab-active .db-tab-count {
          background: rgba(99,102,241,0.3);
          color: #c7d2fe;
        }

        /* ── Content ── */
        .db-content {
          flex: 1;
          overflow-y: auto;
          min-height: 0;
          padding-right: 6px;
        }

        /* ── Campaign Cards Grid ── */
        .db-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
        }
        .db-card {
          padding: 20px;
          border-radius: 16px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.07);
          cursor: pointer;
          display: flex;
          flex-direction: column;
          gap: 14px;
          transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
        }
        .db-card:hover {
          background: rgba(255,255,255,0.06);
          border-color: rgba(99,102,241,0.25);
          box-shadow: 0 12px 40px rgba(0,0,0,0.25), 0 0 0 1px rgba(99,102,241,0.1);
        }
        .db-card-top {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .db-card-brand-icon {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.2));
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 1rem;
          color: #a5b4fc;
          flex-shrink: 0;
          border: 1px solid rgba(99,102,241,0.15);
        }
        .db-card-meta {
          flex: 1;
          min-width: 0;
        }
        .db-card-brand {
          margin: 0;
          font-size: 1rem;
          font-weight: 700;
          color: white;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .db-card-date {
          font-size: 0.7rem;
          color: rgba(255,255,255,0.35);
          display: flex;
          align-items: center;
          gap: 4px;
          margin-top: 2px;
        }
        .db-card-arrow {
          color: rgba(255,255,255,0.15);
          transition: all 0.3s;
          flex-shrink: 0;
        }
        .db-card:hover .db-card-arrow {
          color: rgba(99,102,241,0.7);
          transform: translateX(2px);
        }
        .db-card-product {
          font-size: 0.88rem;
          color: rgba(255,255,255,0.55);
          margin: 0;
          line-height: 1.4;
        }
        .db-card-bottom {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin-top: auto;
        }
        .db-card-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border-radius: 8px;
          font-size: 0.65rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          background: rgba(99,102,241,0.12);
          color: #a5b4fc;
          border: 1px solid rgba(99,102,241,0.15);
        }
        .db-card-badge-green {
          background: rgba(16,185,129,0.1);
          color: #6ee7b7;
          border-color: rgba(16,185,129,0.15);
        }
        .db-card-badge-amber {
          background: rgba(245,158,11,0.1);
          color: #fcd34d;
          border-color: rgba(245,158,11,0.15);
        }

        /* ── Empty States ── */
        .db-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 80px 20px;
          text-align: center;
          gap: 12px;
        }
        .db-empty-icon {
          width: 80px;
          height: 80px;
          border-radius: 24px;
          background: rgba(99,102,241,0.08);
          border: 1px solid rgba(99,102,241,0.12);
          display: flex;
          align-items: center;
          justify-content: center;
          color: rgba(99,102,241,0.5);
          margin-bottom: 8px;
        }
        .db-empty h3 {
          font-size: 1.2rem;
          font-weight: 700;
          color: rgba(255,255,255,0.75);
          margin: 0;
        }
        .db-empty p {
          font-size: 0.88rem;
          color: rgba(255,255,255,0.35);
          margin: 0 0 8px;
          max-width: 300px;
        }

        /* ── Asset Grid ── */
        .db-asset-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
          gap: 16px;
        }
        .db-asset-card {
          padding: 12px;
          border-radius: 14px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          display: flex;
          flex-direction: column;
          gap: 10px;
          cursor: default;
          transition: all 0.3s ease;
        }
        .db-asset-card:hover {
          border-color: rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.05);
        }
        .db-asset-img-wrap {
          width: 100%;
          height: 130px;
          border-radius: 10px;
          overflow: hidden;
          background: rgba(0,0,0,0.3);
        }
        .db-asset-img-wrap img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.3s ease;
        }
        .db-asset-card:hover .db-asset-img-wrap img {
          transform: scale(1.05);
        }
        .avatar-img-wrap {
          border-radius: 50% !important;
          height: 120px;
          width: 120px;
          margin: 0 auto;
        }
        .db-asset-name {
          font-size: 0.78rem;
          margin: 0;
          color: rgba(255,255,255,0.7);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          text-align: center;
        }
        .db-asset-date {
          font-size: 0.68rem;
          color: rgba(255,255,255,0.3);
          text-align: center;
        }

        /* ── Campaign Detail View ── */
        .db-detail {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .db-detail-header {
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .db-detail-back {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          color: rgba(255,255,255,0.6);
          padding: 8px 16px;
          border-radius: 10px;
          font-size: 0.82rem;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: 16px;
          font-weight: 500;
        }
        .db-detail-back:hover {
          background: rgba(255,255,255,0.07);
          color: white;
        }
        .db-detail-title-row {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }
        .db-detail-title {
          font-size: 1.4rem;
          margin: 0 0 10px;
          font-weight: 700;
          color: white;
        }
        .db-detail-platform {
          display: inline-flex;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          padding: 4px 14px;
          border-radius: 8px;
          font-size: 0.7rem;
          text-transform: uppercase;
          font-weight: 800;
          letter-spacing: 0.5px;
          color: white;
        }
        .db-detail-body {
          display: flex;
          flex-direction: column;
          gap: 28px;
        }
        .db-detail-grid-2col {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }

        /* ── Section Blocks ── */
        .db-section {
          padding: 20px;
          border-radius: 16px;
          background: rgba(255,255,255,0.02);
          border: 1px solid rgba(255,255,255,0.05);
        }
        .db-section-title {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          color: rgba(255,255,255,0.4);
          font-weight: 700;
          margin: 0 0 16px;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .db-section-title::after {
          content: '';
          flex: 1;
          height: 1px;
          background: rgba(255,255,255,0.05);
        }
        .db-section-content {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        /* ── Reused detail styles ── */
        .campaign-meta-row { display: flex; flex-wrap: wrap; gap: 8px; }
        .meta-badge {
          padding: 4px 12px; border-radius: 8px; font-size: 0.68rem;
          font-weight: 700; text-transform: capitalize;
          background: rgba(99,102,241,0.12); color: #a5b4fc;
          border: 1px solid rgba(99,102,241,0.15);
        }
        .meta-badge.funnel { background: rgba(16,185,129,0.12); color: #6ee7b7; border-color: rgba(16,185,129,0.15); }
        .meta-badge.emotion { background: rgba(244,114,182,0.1); color: #f9a8d4; border-color: rgba(244,114,182,0.15); }
        .product-desc { font-size: 0.88rem; line-height: 1.6; color: rgba(255,255,255,0.65); margin: 0; }
        .product-chips { display: flex; flex-wrap: wrap; gap: 6px; }
        .feature-chip {
          padding: 4px 12px; border-radius: 8px; font-size: 0.7rem;
          background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
          color: rgba(255,255,255,0.6);
        }
        .target-user { border-top: 1px solid rgba(255,255,255,0.05); padding-top: 14px; margin-top: 8px; }
        .target-user label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.35); display: block; margin-bottom: 4px; }
        .target-user p { font-size: 0.82rem; line-height: 1.5; margin: 0; color: rgba(255,255,255,0.55); }
        .strategy-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }
        .strategy-card {
          padding: 14px; border-radius: 12px; text-align: center;
          background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
          transition: all 0.25s;
        }
        .strategy-card:hover { background: rgba(255,255,255,0.05); border-color: rgba(99,102,241,0.2); }
        .strategy-card label { display: block; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.35); margin-bottom: 6px; }
        .strategy-card span { font-size: 0.88rem; font-weight: 700; color: #a5b4fc; }
        .scene-flow-row { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; font-size: 0.82rem; color: rgba(255,255,255,0.5); }
        .scene-flow-row label { font-weight: 700; margin-right: 6px; color: rgba(255,255,255,0.4); font-size: 0.7rem; text-transform: uppercase; }
        .flow-step { white-space: nowrap; }
        .scene-row {
          padding: 16px 20px; margin-bottom: 10px; border-radius: 12px;
          background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);
          transition: all 0.25s;
        }
        .scene-row:hover { background: rgba(255,255,255,0.04); border-color: rgba(99,102,241,0.2); }
        .scene-meta { display: flex; gap: 12px; margin-bottom: 8px; }
        .scene-num { font-weight: 800; font-size: 0.78rem; color: #6366f1; }
        .scene-intent { font-size: 0.72rem; color: rgba(255,255,255,0.35); }
        .scene-voiceover { font-size: 0.92rem; line-height: 1.5; margin: 0; color: rgba(255,255,255,0.65); }
        .asset-previews, .avatar-preview-row { display: flex; gap: 10px; flex-wrap: wrap; }
        .mini-preview, .avatar-thumb { width: 80px; height: 80px; object-fit: cover; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
        .avatar-thumb { width: 50px; height: 50px; border-radius: 50%; }
        .info-text { font-size: 0.8rem; color: rgba(255,255,255,0.3); }
        .final-video { width: 100%; max-height: 340px; border-radius: 14px; background: #000; }

        /* ── Responsive ── */
        @media (max-width: 768px) {
          .db-root { padding: 16px; gap: 16px; }
          .db-hero { flex-direction: column; align-items: flex-start; gap: 16px; }
          .db-stats-row { grid-template-columns: repeat(2, 1fr); }
          .db-tabs { flex-wrap: wrap; width: 100%; }
          .db-grid { grid-template-columns: 1fr; }
          .db-detail-grid-2col { grid-template-columns: 1fr; }
          .strategy-grid { grid-template-columns: repeat(2, 1fr); }
        }
      `}</style>
    </div>
  );
}

export default Dashboard;

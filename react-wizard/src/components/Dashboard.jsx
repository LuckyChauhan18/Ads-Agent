import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Layout as LayoutIcon, Image as ImageIcon, FileText, User, ArrowLeft, ExternalLink, Calendar, Trash2, Edit2 } from 'lucide-react';
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

  if (loading) return <div className="loading-state">Loading your universe...</div>;

  return (
    <div className="dashboard-container glass">
      <header className="dashboard-header">
        <Link to="/" className="back-btn">
          <ArrowLeft size={18} /> Back to Generator
        </Link>
        <div className="user-profile">
          <div className="avatar-circle">
            {user?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="user-info">
            <h3>{data?.user_info?.full_name || user}</h3>
            <p>{data?.user_info?.email || 'Creator'}</p>
          </div>
        </div>
      </header>

      <nav className="dashboard-nav">
        {['campaigns'].map(tab => (
          <button
            key={tab}
            className={`nav-item active`}
          >
            Campaign Tickets
          </button>
        ))}
      </nav>

      <div className="dashboard-content">
        {activeTab === 'campaigns' && (
          <div className="campaigns-view">
            {!selectedCampaign ? (
              <div className="grid">
                {data?.campaigns?.length > 0 ? data.campaigns.map(c => (
                  <motion.div
                    key={c._id}
                    className="item-card glass-vibrant clickable"
                    layout
                    onClick={() => setSelectedCampaign(c)}
                  >
                    <div className="item-header">
                      <h4>{c.brand_name}</h4>
                      <span className="date-tag"><Calendar size={12} /> {new Date(c.updated_at).toLocaleDateString()}</span>
                    </div>
                    <p className="item-desc">{c.product_name}</p>
                    <div className="item-footer">
                      <span className="badge">{c.platform}</span>
                      <button className="view-btn"><ExternalLink size={14} /></button>
                    </div>
                  </motion.div>
                )) : <p className="empty">No campaigns yet. Let's create one!</p>}
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="campaign-detail-view glass"
              >
                <div className="detail-header">
                  <button className="back-link" onClick={() => setSelectedCampaign(null)}>
                    <ArrowLeft size={16} /> Back to List
                  </button>
                  <div className="title-row">
                    <h2>{selectedCampaign.brand_name}: {selectedCampaign.product_name}</h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className="platform-tag">{selectedCampaign.platform}</span>
                      <button
                        className="btn btn-premium"
                        style={{ padding: '6px 16px', fontSize: '0.8rem', borderRadius: '12px' }}
                        onClick={() => {
                          const campaignAssets = {
                            product_logo: selectedCampaign.product_logo,
                            product_images: selectedCampaign.product_images || [],
                          };
                          navigate('/', { state: { editCampaign: { ...selectedCampaign, ...campaignAssets } } })
                        }}
                      >
                        <Edit2 size={14} /> Recreate
                      </button>
                    </div>
                  </div>
                </div>

                <div className="detail-scroll-content">
                  {/* Campaign Meta Badges */}
                  <div className="campaign-meta-row">
                    {selectedCampaign.funnel_stage && (
                      <span className="meta-badge funnel">{selectedCampaign.funnel_stage} funnel</span>
                    )}
                    {selectedCampaign.ad_length && (
                      <span className="meta-badge">{selectedCampaign.ad_length}s video</span>
                    )}
                    {selectedCampaign.primary_emotions?.map((e, i) => (
                      <span key={i} className="meta-badge emotion">{e}</span>
                    ))}
                  </div>

                  {/* Product Overview from campaign_psychology */}
                  {selectedCampaign.campaign_psychology?.product_understanding && (
                    <section className="detail-section">
                      <h3>Product Overview</h3>
                      <div className="product-overview glass-brutal">
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

                  {/* Strategy Blueprint from pattern_blueprint */}
                  {selectedCampaign.pattern_blueprint?.pattern_blueprint && (
                    <section className="detail-section">
                      <h3>Strategy Blueprint</h3>
                      <div className="strategy-grid">
                        {[
                          { label: 'Hook', value: selectedCampaign.pattern_blueprint.pattern_blueprint.hook_type },
                          { label: 'Tone', value: selectedCampaign.pattern_blueprint.pattern_blueprint.tone },
                          { label: 'Angle', value: selectedCampaign.pattern_blueprint.pattern_blueprint.angle },
                          { label: 'CTA', value: selectedCampaign.pattern_blueprint.pattern_blueprint.cta },
                          { label: 'Text Density', value: selectedCampaign.pattern_blueprint.pattern_blueprint.text_density },
                          { label: 'Opening', value: selectedCampaign.pattern_blueprint.pattern_blueprint.opening_style },
                        ].filter(item => item.value).map((item, i) => (
                          <div key={i} className="strategy-card glass-brutal">
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

                  {/* Storyboard & Script */}
                  <section className="detail-section">
                    <h3>Storyboard & Script</h3>
                    <div className="storyboard-list">
                      {selectedCampaign.final_storyboard?.scenes?.map((scene, i) => (
                        <div key={i} className="scene-row glass-brutal">
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

                  <div className="detail-grid">
                    <section className="detail-section">
                      <h3>Visual Assets</h3>
                      <div className="asset-previews" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                        {selectedCampaign.product_images && selectedCampaign.product_images.length > 0 && (
                          <div className="asset-item" style={{ flex: 1 }}>
                            <label>Product Images</label>
                            <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                              {selectedCampaign.product_images.map((imgUrl, idx) => (
                                <img key={idx} src={imgUrl} alt={`Product ${idx}`} style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }} />
                              ))}
                            </div>
                          </div>
                        )}
                        {selectedCampaign.product_logo && (
                          <div className="asset-item" style={{ flex: 1 }}>
                            <label>Brand Logo</label>
                            <img src={selectedCampaign.product_logo} alt="Logo" style={{ width: '80px', height: '80px', objectFit: 'contain', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', marginTop: '8px', padding: '4px' }} />
                          </div>
                        )}
                        {(!selectedCampaign.product_images || selectedCampaign.product_images.length === 0) && !selectedCampaign.product_logo && (
                          <p className="info-text">No uploaded assets found for this campaign.</p>
                        )}
                      </div>
                    </section>

                    <section className="detail-section">
                      <h3>Avatar Configuration</h3>
                      <div className="avatar-info">
                        {selectedCampaign.avatar_config ? (
                          <div className="avatar-preview-row">
                            {selectedCampaign.avatar_config.selected_avatars?.map((av, i) => (
                              <img key={i} src={av.url} alt="Avatar" className="avatar-thumb" />
                            )) || <p className="info-text">Single avatar used.</p>}
                          </div>
                        ) : <p className="info-text">Avatar will appear after selection.</p>}
                      </div>
                    </section>
                  </div>

                  {selectedCampaign.video_url && (
                    <section className="detail-section">
                      <h3>Generated Video</h3>
                      <div className="video-container">
                        <video controls src={selectedCampaign.video_url} className="final-video" />
                      </div>
                    </section>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        )}
        {/* Removed legacy independent asset grids. Visuals are now strictly bound inside Campaign tickets. */}
      </div>

      <style>{`
        .dashboard-container {
          width: 100%;
          flex: 1;
          min-height: 0;
          display: flex;
          flex-direction: column;
          padding: 24px 40px 40px;
          margin: 0 auto;
          max-width: 1400px;
        }
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
        }
        .user-profile {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .avatar-circle {
            width: 48px;
            height: 48px;
            background: var(--primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2rem;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
        .user-info h3 { font-size: 1.1rem; margin: 0; }
        .user-info p { font-size: 0.8rem; opacity: 0.6; margin: 0; }

        .dashboard-nav {
          display: flex;
          gap: 20px;
          margin-bottom: 30px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          padding-bottom: 10px;
        }
        .nav-item {
          background: transparent;
          border: none;
          color: rgba(255,255,255,0.5);
          cursor: pointer;
          font-weight: 500;
          padding: 8px 4px;
          position: relative;
        }
        .nav-item.active {
          color: white;
        }
        .nav-item.active::after {
          content: '';
          position: absolute;
          bottom: -11px;
          left: 0;
          width: 100%;
          height: 2px;
          background: var(--primary);
        }

        .dashboard-content {
          flex: 1;
          overflow-y: auto;
          padding-right: 10px;
          min-height: 0;
        }
        .item-card.clickable {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .item-card.clickable:hover {
            transform: translateY(-4px) scale(1.02);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }
        
        /* Detail View Styles */
        .campaigns-view {
          display: flex;
          flex-direction: column;
        }
        .campaign-detail-view {
          display: flex;
          flex-direction: column;
          padding: 24px;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 16px;
        }
        .detail-header {
          margin-bottom: 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          padding-bottom: 15px;
        }
        .back-link {
          background: transparent;
          border: none;
          color: var(--primary);
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.85rem;
          margin-bottom: 12px;
          cursor: pointer;
        }
        .title-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .title-row h2 { margin: 0; font-size: 1.4rem; color: #fff; }
        .platform-tag {
          background: var(--primary);
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 0.75rem;
          text-transform: uppercase;
          font-weight: 700;
        }
        .detail-scroll-content {
          padding-right: 12px;
          padding-bottom: 20px;
          display: flex;
          flex-direction: column;
          gap: 30px;
        }
        .detail-section h3 {
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.6;
          margin-bottom: 15px;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .detail-section h3::after {
          content: '';
          flex: 1;
          height: 1px;
          background: rgba(255,255,255,0.05);
        }
        .scene-row {
          padding: 18px 24px;
          margin-bottom: 15px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          transition: all 0.3s ease;
        }
        .scene-row:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(99, 102, 241, 0.3);
          transform: translateY(-2px);
        }
        .scene-meta {
          display: flex;
          gap: 12px;
          margin-bottom: 8px;
        }
        .scene-num { font-weight: 700; font-size: 0.8rem; color: var(--primary); }
        .scene-intent { font-size: 0.75rem; opacity: 0.5; }
        .scene-voiceover { font-size: 0.95rem; line-height: 1.5; margin: 0; }
        
        .detail-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        .asset-previews, .avatar-preview-row {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }
        .mini-preview, .avatar-thumb {
          width: 80px;
          height: 80px;
          object-fit: cover;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.1);
        }
        .avatar-thumb {
          width: 50px;
          height: 50px;
          border-radius: 50%;
        }
        .info-text { font-size: 0.8rem; opacity: 0.4; }

        /* Campaign Meta Badges */
        .campaign-meta-row {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 5px;
        }
        .meta-badge {
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 0.7rem;
          font-weight: 600;
          text-transform: capitalize;
          background: rgba(99, 102, 241, 0.15);
          color: #a5b4fc;
          border: 1px solid rgba(99, 102, 241, 0.2);
        }
        .meta-badge.funnel {
          background: rgba(16, 185, 129, 0.15);
          color: #6ee7b7;
          border-color: rgba(16, 185, 129, 0.2);
        }
        .meta-badge.emotion {
          background: rgba(244, 114, 182, 0.12);
          color: #f9a8d4;
          border-color: rgba(244, 114, 182, 0.2);
        }

        /* Product Overview */
        .product-overview {
          padding: 18px;
          border-radius: 12px;
          background: rgba(255,255,255,0.02);
        }
        .product-desc {
          font-size: 0.85rem;
          line-height: 1.6;
          opacity: 0.8;
          margin: 0 0 14px;
        }
        .product-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-bottom: 14px;
        }
        .feature-chip {
          padding: 3px 10px;
          border-radius: 12px;
          font-size: 0.65rem;
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.08);
          opacity: 0.7;
        }
        .target-user {
          border-top: 1px solid rgba(255,255,255,0.05);
          padding-top: 12px;
        }
        .target-user label {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.4;
          display: block;
          margin-bottom: 4px;
        }
        .target-user p { font-size: 0.8rem; line-height: 1.5; margin: 0; opacity: 0.7; }

        /* Strategy Grid */
        .strategy-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-bottom: 12px;
        }
        .strategy-card {
          padding: 12px;
          border-radius: 10px;
          background: rgba(255,255,255,0.03);
          text-align: center;
        }
        .strategy-card label {
          display: block;
          font-size: 0.6rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          opacity: 0.4;
          margin-bottom: 6px;
        }
        .strategy-card span {
          font-size: 0.85rem;
          font-weight: 600;
          color: #a5b4fc;
        }
        .scene-flow-row {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 4px;
          font-size: 0.8rem;
          opacity: 0.6;
        }
        .scene-flow-row label {
          font-weight: 600;
          margin-right: 6px;
          opacity: 0.5;
          font-size: 0.7rem;
          text-transform: uppercase;
        }
        .flow-step { white-space: nowrap; }

        .final-video {
          width: 100%;
          max-height: 300px;
          border-radius: 12px;
          background: #000;
        }

        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
          gap: 20px;
        }
        .asset-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 20px;
        }
        .item-card {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .item-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        .date-tag {
            font-size: 0.7rem;
            opacity: 0.5;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .item-desc {
            font-size: 0.9rem;
            opacity: 0.8;
            margin: 0;
        }
        .item-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: auto;
        }
        .badge {
            background: rgba(255,255,255,0.1);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.7rem;
            text-transform: uppercase;
        }
        .asset-card {
          padding: 10px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .asset-card img {
          width: 100%;
          height: 120px;
          object-fit: cover;
          border-radius: 8px;
        }
        .asset-info p {
          font-size: 0.75rem;
          margin: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .empty {
          text-align: center;
          opacity: 0.5;
          margin-top: 100px;
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
            transition: all 0.2s;
        }
        .back-btn:hover {
            background: rgba(255,255,255,0.05);
        }
      `}</style>
    </div>
  );
}

export default Dashboard;

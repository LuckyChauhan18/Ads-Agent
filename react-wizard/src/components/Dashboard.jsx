import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Layout as LayoutIcon, Image as ImageIcon, FileText, User, ArrowLeft, ExternalLink, Calendar, Trash2 } from 'lucide-react';
import { workflowService } from '../services/api';

function Dashboard({ user }) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [activeTab, setActiveTab] = React.useState('campaigns');
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
        {['campaigns', 'logos', 'products', 'avatars'].map(tab => (
          <button
            key={tab}
            className={`nav-item ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      <div className="dashboard-content">
        {activeTab === 'campaigns' && (
          <div className="grid">
            {data?.campaigns?.length > 0 ? data.campaigns.map(c => (
              <motion.div key={c._id} className="item-card glass-vibrant" layout>
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
        )}

        {activeTab === 'logos' && (
          <div className="asset-grid">
            {data?.assets?.logos?.length > 0 ? data.assets.logos.map(l => (
              <div key={l.id} className="asset-card glass">
                <img src={`http://localhost:8000${l.url}`} alt="Logo" />
                <div className="asset-info">
                  <p>{l.filename}</p>
                </div>
              </div>
            )) : <p className="empty">No logos uploaded yet.</p>}
          </div>
        )}

        {activeTab === 'products' && (
          <div className="asset-grid">
            {data?.assets?.products?.length > 0 ? data.assets.products.map(p => (
              <div key={p.id} className="asset-card glass">
                <img src={`http://localhost:8000${p.url}`} alt="Product" />
                <div className="asset-info">
                  <p>{p.filename}</p>
                </div>
              </div>
            )) : <p className="empty">No product images yet.</p>}
          </div>
        )}

        {activeTab === 'avatars' && (
          <div className="asset-grid">
            {data?.assets?.avatars?.length > 0 ? data.assets.avatars.map(a => (
              <div key={a.id} className="asset-card glass">
                <img src={`http://localhost:8000${a.url}`} alt="Avatar" />
                <div className="asset-info">
                  <p>{a.filename}</p>
                </div>
              </div>
            )) : <p className="empty">No AI avatars generated yet.</p>}
          </div>
        )}
      </div>

      <style>{`
        .dashboard-container {
          width: 900px;
          height: 700px;
          padding: 40px;
          display: flex;
          flex-direction: column;
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

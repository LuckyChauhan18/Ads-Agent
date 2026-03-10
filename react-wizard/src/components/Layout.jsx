import React from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Layout as LayoutIcon, LogOut, Sparkles, BarChart3, Send } from 'lucide-react';

const Layout = ({ children, user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="layout-shell">
      <div className="glass-container">
        <header className="layout-header">
          <h1
            className="premium-logo"
            onClick={() => navigate('/')}
            style={{ cursor: 'pointer' }}
          >
            SPECTRA
          </h1>

          <nav className="header-nav">
            <Link to="/" className={`nav-btn glass ${path === '/' ? 'nav-active' : ''}`}>
              <Sparkles size={16} /> Create
            </Link>
            <Link to="/dashboard" className={`nav-btn glass ${path === '/dashboard' ? 'nav-active' : ''}`}>
              <LayoutIcon size={16} /> Dashboard
            </Link>
            <Link to="/analytics" className={`nav-btn glass ${path === '/analytics' ? 'nav-active' : ''}`}>
              <BarChart3 size={16} /> Analytics
            </Link>
            <Link to="/publish" className={`nav-btn glass ${path === '/publish' ? 'nav-active' : ''}`}>
              <Send size={16} /> Publish
            </Link>
          </nav>

          <div className="header-actions">
            <span className="user-pill">{user || 'User'}</span>
            <button className="nav-btn glass logout-btn" onClick={onLogout}>
              <LogOut size={16} />
            </button>
          </div>
        </header>

        <main className="layout-content">
          {children}
        </main>
      </div>

      <style>{`
        .layout-shell {
          width: 100vw;
          height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          overflow: hidden;
        }
        .layout-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
          padding-bottom: 16px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          margin-bottom: 16px;
          flex-shrink: 0;
          gap: 16px;
        }
        .header-nav {
          display: flex;
          gap: 6px;
          flex: 1;
          justify-content: center;
        }
        .header-actions {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .user-pill {
          padding: 6px 14px;
          border-radius: 20px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.2);
          font-size: 0.75rem;
          color: #a5b4fc;
          font-weight: 600;
        }
        .logout-btn {
          border-color: rgba(255, 100, 100, 0.2) !important;
          color: rgba(255, 150, 150, 0.8) !important;
          padding: 8px 12px !important;
        }
        .logout-btn:hover {
          background: rgba(255, 100, 100, 0.1) !important;
        }
        .nav-btn {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          color: rgba(255, 255, 255, 0.6);
          padding: 8px 16px;
          border-radius: 14px;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.8rem;
          cursor: pointer;
          text-decoration: none;
          transition: all 0.3s ease;
          font-weight: 500;
        }
        .nav-btn:hover {
          background: rgba(255, 255, 255, 0.08);
          color: white;
        }
        .nav-btn.nav-active {
          background: rgba(99, 102, 241, 0.12);
          border-color: rgba(99, 102, 241, 0.3);
          color: #a5b4fc;
        }
        .layout-content {
          flex: 1;
          width: 100%;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          min-height: 0;
        }

        @media (max-width: 900px) {
          .header-nav { gap: 4px; }
          .nav-btn { padding: 6px 10px; font-size: 0.7rem; }
        }
      `}</style>
    </div>
  );
};

export default Layout;

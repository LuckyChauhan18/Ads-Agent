import React from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Layout as LayoutIcon, LogOut, Sparkles } from 'lucide-react';

const Layout = ({ children, user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="layout-shell">
      <div className="glass-container">
        <header className="layout-header">
          <h1
            className="premium-logo"
            onClick={() => navigate('/')}
            style={{ cursor: 'pointer' }}
          >
            AD<span className="highlight">GEN</span>
          </h1>

          <div className="header-actions">
            {location.pathname !== '/dashboard' ? (
              <Link to="/dashboard" className="nav-btn glass">
                <LayoutIcon size={18} /> Dashboard
              </Link>
            ) : (
              <Link to="/" className="nav-btn glass">
                <Sparkles size={18} /> Ad Creator
              </Link>
            )}

            <button className="nav-btn glass logout-btn" onClick={onLogout}>
              <LogOut size={16} /> Logout
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
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          margin-bottom: 20px;
          flex-shrink: 0;
        }
        .header-actions {
            display: flex;
            gap: 12px;
        }
        .logout-btn {
            border-color: rgba(255, 100, 100, 0.2) !important;
            color: rgba(255, 150, 150, 0.8) !important;
        }
        .logout-btn:hover {
            background: rgba(255, 100, 100, 0.1) !important;
        }
        .nav-btn {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: white;
          padding: 10px 20px;
          border-radius: 20px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.9rem;
          cursor: pointer;
          text-decoration: none;
          transition: all 0.3s ease;
        }
        .nav-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          transform: translateY(-2px);
        }
        .layout-content {
          flex: 1;
          width: 100%;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }
      `}</style>
    </div>
  );
};

export default Layout;

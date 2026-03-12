import React from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Layout as LayoutIcon, LogOut, Sparkles, BarChart3, Send, User, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const path = location.pathname;
  const { user, logout } = useAuth();

  const navItems = [
    { path: '/create', icon: Sparkles, label: 'Create', description: 'Generate new campaigns' },
    { path: '/dashboard', icon: LayoutIcon, label: 'Dashboard', description: 'View all campaigns' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics', description: 'Track performance' },
    { path: '/publish', icon: Send, label: 'Publish', description: 'Share your ads' },
  ];

  return (
    <div className="layout-shell">
      <aside className="sidebar-nav">
        {/* Logo Section */}
        <div className="sidebar-header">
          <div className="logo-container" onClick={() => navigate('/create')}>
            <Zap className="logo-icon" size={28} />
            <h1 className="logo-text">SPECTRA</h1>
          </div>
          <div className="brand-tagline">AI Ad Studio</div>
        </div>

        {/* Navigation Items */}
        <nav className="nav-menu">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = path === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${isActive ? 'nav-item-active' : ''}`}
              >
                <div className="nav-icon-wrapper">
                  <Icon className="nav-icon" size={20} />
                </div>
                <div className="nav-text">
                  <span className="nav-label">{item.label}</span>
                  <span className="nav-description">{item.description}</span>
                </div>
                {isActive && (
                  <motion.div
                    className="active-indicator"
                    layoutId="activeTab"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User Profile & Logout */}
        <div className="sidebar-footer">
          <div className="user-profile-card">
            <div className="user-avatar">
              <User size={18} />
            </div>
            <div className="user-details">
              <span className="user-name">{user?.username || user?.full_name || 'User'}</span>
              <span className="user-status">Active</span>
            </div>
          </div>
          <button className="logout-btn" onClick={logout} title="Logout">
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <div className="main-wrapper">
        <main className="layout-content">
          {children}
        </main>
      </div>

      <style>{`
        .layout-shell {
          width: 100vw;
          height: 100vh;
          display: flex;
          overflow: hidden;
          background: linear-gradient(135deg, #0a0a1f 0%, #1a0a2e 50%, #0f0f23 100%);
          position: relative;
        }

        .layout-shell::before {
          content: '';
          position: absolute;
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
          border-radius: 50%;
          top: -200px;
          right: -200px;
          filter: blur(100px);
          pointer-events: none;
          animation: float-blob 15s ease-in-out infinite;
        }

        .layout-shell::after {
          content: '';
          position: absolute;
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, rgba(168, 85, 247, 0.12) 0%, transparent 70%);
          border-radius: 50%;
          bottom: -150px;
          left: -150px;
          filter: blur(100px);
          pointer-events: none;
          animation: float-blob 20s ease-in-out infinite reverse;
        }

        @keyframes float-blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          50% {
            transform: translate(30px, -30px) scale(1.1);
          }
        }

        /* Sidebar Navigation */
        .sidebar-nav {
          width: 280px;
          height: 100vh;
          background: rgba(15, 15, 30, 0.6);
          backdrop-filter: blur(20px);
          border-right: 1px solid rgba(255, 255, 255, 0.08);
          display: flex;
          flex-direction: column;
          padding: 24px 16px;
          gap: 24px;
          flex-shrink: 0;
          box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
        }

        /* Logo Section */
        .sidebar-header {
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding: 8px 12px;
        }

        .logo-container {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .logo-container:hover {
          transform: translateX(4px);
        }

        .logo-icon {
          color: #6366f1;
          filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.6));
          animation: pulse-glow 3s ease-in-out infinite;
        }

        @keyframes pulse-glow {
          0%, 100% { filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.6)); }
          50% { filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.8)); }
        }

        .logo-text {
          font-size: 1.8rem;
          font-weight: 900;
          background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: 2px;
          margin: 0;
        }

        .brand-tagline {
          font-size: 0.7rem;
          color: rgba(255, 255, 255, 0.4);
          text-transform: uppercase;
          letter-spacing: 2px;
          margin-left: 40px;
          font-weight: 600;
        }

        /* Navigation Menu */
        .nav-menu {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;
          overflow-y: auto;
          padding: 0 4px;
        }

        .nav-menu::-webkit-scrollbar {
          width: 4px;
        }

        .nav-menu::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 14px 16px;
          border-radius: 14px;
          background: transparent;
          border: 1px solid transparent;
          color: rgba(255, 255, 255, 0.6);
          text-decoration: none;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          position: relative;
          overflow: hidden;
        }

        .nav-item::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent);
          transition: left 0.5s;
        }

        .nav-item:hover::before {
          left: 100%;
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.1);
          color: white;
          transform: translateX(4px);
        }

        .nav-item-active {
          background: rgba(99, 102, 241, 0.15) !important;
          border-color: rgba(99, 102, 241, 0.3) !important;
          color: #c7d2fe !important;
          box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);
        }

        .nav-item-active .nav-icon {
          color: #6366f1;
          filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
        }

        .nav-icon-wrapper {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .nav-icon {
          transition: all 0.3s;
        }

        .nav-item:hover .nav-icon {
          transform: scale(1.1);
        }

        .nav-text {
          display: flex;
          flex-direction: column;
          gap: 2px;
          flex: 1;
        }

        .nav-label {
          font-size: 0.95rem;
          font-weight: 600;
          line-height: 1.2;
        }

        .nav-description {
          font-size: 0.7rem;
          opacity: 0.6;
          line-height: 1.2;
        }

        .active-indicator {
          position: absolute;
          right: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 4px;
          height: 60%;
          background: linear-gradient(180deg, #6366f1 0%, #a855f7 100%);
          border-radius: 4px 0 0 4px;
          box-shadow: 0 0 12px rgba(99, 102, 241, 0.6);
        }

        /* Sidebar Footer - User Profile */
        .sidebar-footer {
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding-top: 20px;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .user-profile-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.06);
          transition: all 0.3s;
        }

        .user-profile-card:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(99, 102, 241, 0.2);
        }

        .user-avatar {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
          flex-shrink: 0;
        }

        .user-details {
          display: flex;
          flex-direction: column;
          gap: 2px;
          flex: 1;
          min-width: 0;
        }

        .user-name {
          font-size: 0.9rem;
          font-weight: 600;
          color: white;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .user-status {
          font-size: 0.7rem;
          color: #10b981;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .user-status::before {
          content: '';
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #10b981;
          display: inline-block;
          animation: pulse-dot 2s ease-in-out infinite;
        }

        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(0.8); }
        }

        .logout-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px;
          border-radius: 10px;
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.15);
          color: #fca5a5;
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .logout-btn:hover {
          background: rgba(239, 68, 68, 0.15);
          border-color: rgba(239, 68, 68, 0.3);
          color: #fecaca;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
        }

        .logout-btn:active {
          transform: translateY(0);
        }

        /* Main Content Wrapper */
        .main-wrapper {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          min-width: 0;
        }

        .layout-content {
          flex: 1;
          width: 100%;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          min-height: 0;
        }

        /* Responsive Design */
        @media (max-width: 1024px) {
          .sidebar-nav {
            width: 240px;
          }

          .nav-description {
            display: none;
          }

          .brand-tagline {
            font-size: 0.6rem;
          }
        }

        @media (max-width: 768px) {
          .sidebar-nav {
            width: 70px;
            padding: 20px 8px;
          }

          .sidebar-header {
            align-items: center;
          }

          .logo-text,
          .brand-tagline {
            display: none;
          }

          .logo-icon {
            margin: 0 auto;
          }

          .nav-item {
            justify-content: center;
            padding: 14px 8px;
          }

          .nav-text {
            display: none;
          }

          .user-profile-card {
            flex-direction: column;
            padding: 10px;
          }

          .user-details {
            display: none;
          }

          .logout-btn span {
            display: none;
          }

          .logout-btn {
            padding: 12px;
          }
        }
      `}</style>
    </div>
  );
};

export default Layout;

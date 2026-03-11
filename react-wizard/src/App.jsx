import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Pages (full-page routed views)
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import PublishCenter from './pages/PublishCenter';

// Layout & routing
import ProtectedRoute from './components/layout/ProtectedRoute';
import Layout from './components/layout/Layout';

// Wizard
import Wizard from './components/wizard/Wizard';

import './index.css';


function App() {
  const [user, setUser] = useState(localStorage.getItem('spectra_user'));

  const handleLogout = () => {
    localStorage.removeItem('spectra_token');
    localStorage.removeItem('spectra_user');
    setUser(null);
    window.location.href = '/auth';
  };

  const handleLogin = (username) => {
    setUser(username);
  };

  return (
    <Router>
      <Routes>
        {/* Auth Route */}
        <Route
          path="/auth"
          element={
            <div className="app-container">
              <div className="bg-layer bg-auth" />
              <AuthPage onLogin={handleLogin} />
            </div>
          }
        />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={handleLogout}>
                <Wizard />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={handleLogout}>
                <Dashboard user={user} />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={handleLogout}>
                <AnalyticsDashboard user={user} />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/publish"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={handleLogout}>
                <PublishCenter user={user} />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <style>{`
        .app-container {
          width: 100vw;
          height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
        }

        .bg-layer {
          position: absolute;
          inset: 0;
          z-index: -1;
          transition: background 1s ease;
        }

        .bg-auth { background: radial-gradient(circle at 70% 30%, #1e1b4b 0%, #020617 100%); }
        .bg-dashboard { background: radial-gradient(circle at 30% 70%, #171717 0%, #0a0a0a 100%); }

        .bg-step-1 { background: radial-gradient(circle at 20% 20%, #1e1b4b 0%, #020617 100%); }
        .bg-step-2 { background: radial-gradient(circle at 80% 20%, #312e81 0%, #020617 100%); }
        .bg-step-3 { background: radial-gradient(circle at 20% 80%, #1e1b4b 0%, #020617 100%); }
        .bg-step-4 { background: radial-gradient(circle at 80% 80%, #3730a3 0%, #020617 100%); }
        .bg-step-5 { background: radial-gradient(circle at 50% 50%, #1e1b4b 0%, #020617 100%); }
        .bg-step-6 { background: radial-gradient(circle at 10% 50%, #312e81 0%, #020617 100%); }
        .bg-step-7 { background: radial-gradient(circle at 90% 50%, #1e1b4b 0%, #020617 100%); }
        .bg-step-8 { background: radial-gradient(circle at 50% 10%, #4338ca 0%, #020617 100%); }
        .bg-step-9 { background: radial-gradient(circle at 50% 90%, #1e1b4b 0%, #020617 100%); }

        .header {
          padding: 24px 40px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .premium-logo {
          font-size: 1.5rem;
          font-weight: 800;
          letter-spacing: -1px;
          color: white;
          margin: 0;
        }

        .premium-logo .highlight {
          color: #818cf8;
          text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
        }

        .main-content {
          flex: 1;
          overflow-y: auto;
          padding: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .footer {
          padding: 24px 40px;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
          background: rgba(0, 0, 0, 0.2);
        }

        @media (max-width: 768px) {
          .glass-container {
            width: 100vw;
            height: 100vh;
            border-radius: 0;
          }
          .header, .footer {
            padding: 16px 20px;
          }
          .main-content {
            padding: 20px;
          }
        }
      `}</style>
    </Router>
  );
}

export default App;

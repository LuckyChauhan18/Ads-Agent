import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Loader2 } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #0a0a1f 0%, #1a0a2e 50%, #0f0f23 100%)',
        color: 'white',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <Loader2 size={48} className="animate-spin" style={{ color: '#818cf8' }} />
        <p style={{ fontSize: '14px', opacity: 0.7 }}>Checking authentication...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  return children;
};

export default ProtectedRoute;

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const LoadingOverlay = ({ message, active }) => {
  return (
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="loading-overlay"
        >
          <div className="spinner-container">
            <div className="spinner"></div>
            <p className="loading-msg">{message}</p>
          </div>

          <style>{`
            .loading-overlay {
              position: absolute;
              top: 0;
              left: 0;
              width: 100%;
              height: 100%;
              background: rgba(0, 0, 0, 0.6);
              backdrop-filter: blur(10px);
              z-index: 100;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: 24px;
            }
            .spinner-container {
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 20px;
            }
            .spinner {
              width: 50px;
              height: 50px;
              border: 3px solid rgba(255, 255, 255, 0.1);
              border-top: 3px solid white;
              border-radius: 50%;
              animation: spin 1s linear infinite;
            }
            .loading-msg {
              font-family: 'Outfit', sans-serif;
              font-size: 1.1rem;
              letter-spacing: 0.5px;
            }
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}</style>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default LoadingOverlay;

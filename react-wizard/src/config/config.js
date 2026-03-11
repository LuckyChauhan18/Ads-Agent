/**
 * Application Configuration
 * Reads from environment variables (prefixed with VITE_)
 */

const config = {
  // API Configuration
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  
  // App Configuration
  appName: import.meta.env.VITE_APP_NAME || 'SPECTRA',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
  
  // Feature Flags
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  enableDebug: import.meta.env.VITE_ENABLE_DEBUG === 'true',
  
  // API Timeout (milliseconds)
  apiTimeout: 30000,
  
  // Local Storage Keys
  storageKeys: {
    token: 'spectra_token',
    user: 'spectra_user',
  },
};

// Log configuration in development mode
if (config.enableDebug) {
  console.log('🔧 App Configuration:', config);
}

export default config;

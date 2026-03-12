import axios from 'axios';
import config from '../config/config';

const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: config.apiTimeout,
  withCredentials: true,  // Send cookies with every request
  headers: {
    'Content-Type': 'application/json',
  },
});

// Handle FormData Content-Type
api.interceptors.request.use((reqConfig) => {
  if (reqConfig.data instanceof FormData) {
    delete reqConfig.headers['Content-Type'];
  }
  return reqConfig;
});

// Auto-logout on 401 (skip for login endpoint so the form can show the error)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isLoginRequest = err.config?.url?.includes('/auth/login');
    if (err.response?.status === 401 && !isLoginRequest) {
      // Dispatch logout event for global handling
      window.dispatchEvent(new Event('auth:logout'));
    }
    return Promise.reject(err);
  }
);

export const authService = {
  signup: (username, password, email = '', fullName = '', companyId = '') =>
    api.post('/auth/signup', {
      username,
      password,
      email: email || null,
      full_name: fullName || null,
      company_id: companyId || null,
    }),
  login: (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
};

export const workflowService = {
  runDiscovery: (data) => api.post('/workflow/step/discover', { data }),
  runResearch: (product, curated_brands) =>
    api.post('/workflow/step/research', { data: { product, curated_brands } }, { timeout: config.longOperationTimeout }),
  runPsychology: (data) => api.post('/workflow/step/psychology', { data }, { timeout: config.longOperationTimeout }),
  runScript: (data) => api.post('/workflow/step/script', { data }, { timeout: config.longOperationTimeout }),
  runGenerateAvatars: (gender, style, custom_prompt) =>
    api.post('/workflow/step/avatar/generate', { data: { gender, style, custom_prompt } }, { timeout: config.longOperationTimeout }),
  runRender: (data) => api.post('/workflow/step/render', { data }, { timeout: config.longOperationTimeout }),
  runUploadAssets: (campaignId, assetType, formData) =>
    api.post(`/workflow/upload-assets/${campaignId}/${assetType}`, formData),
  runGetHistory: () => api.get('/workflow/history'),
  runGetDashboard: () => api.get('/workflow/dashboard'),
  runGetAvatarHistory: () => api.get('/workflow/step/avatar/history'),
  submitFeedback: (data) => api.post('/workflow/feedback', data),
  getFeedback: () => api.get('/workflow/feedback'),
};

export const analyticsService = {
  getCampaignAnalytics: (campaignId) => api.get(`/analytics/campaign/${campaignId}`),
  getDashboardAnalytics: () => api.get('/analytics/dashboard'),
  trackEvent: (campaignId, eventType, metadata = {}) =>
    api.post('/analytics/track', { campaign_id: campaignId, event_type: eventType, metadata }),
  seedDemoData: (campaignId) => api.post(`/analytics/seed/${campaignId}`),
};

export const publishService = {
  getConnectedPlatforms: () => api.get('/publish/platforms'),
  connectPlatform: (platform, credentials) =>
    api.post('/publish/platforms/connect', { platform, credentials }),
  disconnectPlatform: (platform) =>
    api.post('/publish/platforms/disconnect', { platform }),
  publishAd: (campaignId, platforms, publishConfig = {}) =>
    api.post('/publish/push', { campaign_id: campaignId, platforms, config: publishConfig }),
  getPublishHistory: (campaignId) => api.get(`/publish/history/${campaignId}`),
};

export const aiAssistService = {
  runGenerateDescription: (formData) => api.post('/ai-assist/generate-description', formData),
  runUploadAvatar: (formData) => api.post('/ai-assist/upload-avatar', formData),
};

export default api;

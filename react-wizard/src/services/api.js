import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth Interceptor
api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  const token = localStorage.getItem('spectra_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('spectra_token');
      localStorage.removeItem('spectra_user');
      window.location.href = '/auth';
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
  getMe: () => api.get('/auth/me'),
};

export const workflowService = {
  runDiscovery: (data) => api.post('/workflow/step/discover', { data }),
  runResearch: (product, curated_brands) =>
    api.post('/workflow/step/research', { data: { product, curated_brands } }),
  runPsychology: (data) => api.post('/workflow/step/psychology', { data }),
  runScript: (data) => api.post('/workflow/step/script', { data }),
  runGenerateAvatars: (gender, style, custom_prompt) =>
    api.post('/workflow/step/avatar/generate', { data: { gender, style, custom_prompt } }),
  runRender: (data) => api.post('/workflow/step/render', { data }),
  runUploadAssets: (campaignId, assetType, formData) =>
    api.post(`/workflow/upload-assets/${campaignId}/${assetType}`, formData),
  runGetHistory: () => api.get('/workflow/history'),
  runGetAvatarHistory: () => api.get('/workflow/avatars/history'),
  runGetDashboard: () => api.get('/workflow/dashboard'),
  submitFeedback: (data) => api.post('/workflow/feedback', data),
  getFeedback: () => api.get('/workflow/feedback'),
};

export const analyticsService = {
  getCampaignAnalytics: (campaignId) => api.get(`/analytics/campaign/${campaignId}`),
  getDashboardAnalytics: () => api.get('/analytics/dashboard'),
  trackEvent: (campaignId, eventType, metadata = {}) =>
    api.post('/analytics/track', { campaign_id: campaignId, event_type: eventType, metadata }),
};

export const publishService = {
  getConnectedPlatforms: () => api.get('/publish/platforms'),
  connectPlatform: (platform, credentials) =>
    api.post('/publish/platforms/connect', { platform, credentials }),
  disconnectPlatform: (platform) =>
    api.post('/publish/platforms/disconnect', { platform }),
  publishAd: (campaignId, platforms, config = {}) =>
    api.post('/publish/push', { campaign_id: campaignId, platforms, config }),
  getPublishHistory: (campaignId) => api.get(`/publish/history/${campaignId}`),
};

export const aiAssistService = {
  runGenerateDescription: (formData) => api.post('/ai-assist/generate-description', formData),
  runUploadAvatar: (formData) => api.post('/ai-assist/upload-avatar', formData),
};

export default api;

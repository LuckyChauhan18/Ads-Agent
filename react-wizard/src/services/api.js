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
    // Let the browser set the boundary by removing the custom Content-Type
    delete config.headers['Content-Type'];
  }
  const token = localStorage.getItem('adgen_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  signup: (username, password, email = '', fullName = '', companyId = '') =>
    api.post('/auth/signup', { username, email, full_name: fullName, company_id: companyId }, { params: { password } }),
  login: (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
};

export const workflowService = {
  runDiscovery: (data) => api.post('/workflow/step/discover', { data }),
  runResearch: (product, curated_brands) => api.post('/workflow/step/research', { data: { product, curated_brands } }),
  runPsychology: (data) => api.post('/workflow/step/psychology', { data }),
  runScript: (data) => api.post('/workflow/step/script', { data }),
  runGenerateAvatars: (gender, style, custom_prompt) => api.post('/workflow/step/avatar/generate', { data: { gender, style, custom_prompt } }),
  runRender: (data) => api.post('/workflow/step/render', { data }),
  runUploadAssets: (campaignId, assetType, formData) => api.post(`/workflow/upload-assets/${campaignId}/${assetType}`, formData),
  runGetHistory: () => api.get('/workflow/history'),
  runGetDashboard: () => api.get('/workflow/dashboard'),
};

export const aiAssistService = {
  runGenerateDescription: (formData) => api.post('/ai-assist/generate-description', formData),
  runUploadAvatar: (formData) => api.post('/ai-assist/upload-avatar', formData),
};

export default api;

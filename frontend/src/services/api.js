import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Create axios instance
const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get('/auth/me'),
  updateProfile: (userData) => api.put('/auth/me', userData),
  changePassword: (passwordData) => api.post('/auth/change-password', passwordData),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken })
};

// Invoices API
export const invoicesAPI = {
  getInvoices: (params) => api.get('/invoices', { params }),
  getInvoice: (id) => api.get(`/invoices/${id}`),
  createInvoice: (invoiceData) => api.post('/invoices', invoiceData),
  updateInvoice: (id, invoiceData) => api.put(`/invoices/${id}`, invoiceData),
  deleteInvoice: (id) => api.delete(`/invoices/${id}`),
  getInvoiceSummary: (period) => api.get('/invoices/stats/summary', { params: { period } }),
  getInvoiceAnalytics: (period) => api.get('/invoices/stats/analytics', { params: { period } }),
  getOverdueInvoices: () => api.get('/invoices/overdue'),
  bulkActions: (action) => api.post('/invoices/bulk-actions', action),
  sendReminder: (id, type) => api.post(`/invoices/${id}/send-reminder`, null, { params: { reminder_type: type } })
};

// CRM API
export const crmAPI = {
  // Customers
  getCustomers: (params) => api.get('/crm/customers', { params }),
  getCustomer: (id) => api.get(`/crm/customers/${id}`),
  createCustomer: (customerData) => api.post('/crm/customers', customerData),
  updateCustomer: (id, customerData) => api.put(`/crm/customers/${id}`, customerData),
  deleteCustomer: (id) => api.delete(`/crm/customers/${id}`),
  getCustomerSummary: () => api.get('/crm/customers/stats/summary'),
  
  // Interactions
  getInteractions: (params) => api.get('/crm/interactions', { params }),
  createInteraction: (interactionData) => api.post('/crm/interactions', interactionData),
  updateInteraction: (id, interactionData) => api.put(`/crm/interactions/${id}`, interactionData),
  
  // Follow-ups
  getPendingFollowUps: () => api.get('/crm/follow-ups')
};

// AI Assistant API
export const aiAPI = {
  query: (queryData) => api.post('/ai/query', queryData),
  getInsights: () => api.get('/ai/insights'),
  getRecommendations: () => api.get('/ai/recommendations'),
  getContext: () => api.get('/ai/context'),
  submitFeedback: (feedback) => api.post('/ai/feedback', feedback),
  getHistory: (limit) => api.get('/ai/history', { params: { limit } }),
  getAnalytics: () => api.get('/ai/analytics'),
  getSmartInsights: (query) => api.post('/ai/smart-insights', null, { params: { query } })
};

// Reports API
export const reportsAPI = {
  generateReport: (reportData) => api.post('/reports/generate', reportData),
  getReports: (params) => api.get('/reports', { params }),
  getReport: (id) => api.get(`/reports/${id}`),
  deleteReport: (id) => api.delete(`/reports/${id}`),
  getDashboard: (period) => api.get('/reports/dashboard', { params: { period } }),
  getAnalyticsOverview: (period) => api.get('/reports/analytics/overview', { params: { period } }),
  getKPIMetrics: (period) => api.get('/reports/metrics/kpi', { params: { period } })
};

// Utility functions
export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    return error.response.data?.detail || error.response.data?.message || 'An error occurred';
  } else if (error.request) {
    // Request was made but no response received
    return 'Network error. Please check your connection.';
  } else {
    // Something else happened
    return 'An unexpected error occurred';
  }
};

export const handleAPIResponse = (response) => {
  if (response.data.success) {
    return response.data.data;
  } else {
    throw new Error(response.data.message || 'Request failed');
  }
};

export default api;
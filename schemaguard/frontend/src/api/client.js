import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/** @type {import('axios').AxiosInstance} */
const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

function clearStoredAuth() {
  localStorage.removeItem('schemaguard_token');
  localStorage.removeItem('schemaguard_user');
}

function isJwtFailure(error) {
  const status = error.response?.status;
  const payload = error.response?.data || {};
  const message = `${payload.msg || payload.message || payload.error || ''}`.toLowerCase();
  return status === 422 && (
    message.includes('token') ||
    message.includes('jwt') ||
    message.includes('signature') ||
    message.includes('segments')
  );
}

client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('schemaguard_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || isJwtFailure(error)) {
      clearStoredAuth();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Authentication API calls.
 * @typedef {{ email: string, password: string }} AuthPayload
 * @typedef {{ access_token: string, user_id: string, email: string }} AuthResponse
 */
export const authAPI = {
  /** @param {AuthPayload} data @returns {Promise<AuthResponse>} */
  register: (data) => client.post('/api/auth/register', data).then((r) => r.data),
  /** @param {AuthPayload} data @returns {Promise<AuthResponse>} */
  login: (data) => client.post('/api/auth/login', data).then((r) => r.data),
  /** @param {{ email: string }} data */
  forgotPassword: (data) => client.post('/api/auth/forgot-password', data).then((r) => r.data),
};

/**
 * Registry API calls.
 * @typedef {{ name: string, description?: string }} CreateRegistryPayload
 */
export const registryAPI = {
  /** @returns {Promise<{ registries: Array, total: number }>} */
  list: () => client.get('/api/registries').then((r) => r.data),
  /** @param {CreateRegistryPayload} data */
  create: (data) => client.post('/api/registries', data).then((r) => r.data),
  /** @param {string} id */
  get: (id) => client.get(`/api/registries/${id}`).then((r) => r.data),
  /** @param {string} id */
  delete: (id) => client.delete(`/api/registries/${id}`),
};

export const collaborationAPI = {
  listMembers: (registryId) =>
    client.get(`/api/registries/${registryId}/members`).then((r) => r.data),
  addMember: (registryId, data) =>
    client.post(`/api/registries/${registryId}/members`, data).then((r) => r.data),
  removeMember: (registryId, memberId) =>
    client.delete(`/api/registries/${registryId}/members/${memberId}`),
  updateMemberRole: (registryId, memberId, data) =>
    client.patch(`/api/registries/${registryId}/members/${memberId}/role`, data).then((r) => r.data),
  listSubscribers: (registryId) =>
    client.get(`/api/registries/${registryId}/subscribers`).then((r) => r.data),
  addSubscriber: (registryId, data) =>
    client.post(`/api/registries/${registryId}/subscribers`, data).then((r) => r.data),
  removeSubscriber: (registryId, subscriberId) =>
    client.delete(`/api/registries/${registryId}/subscribers/${subscriberId}`),
  makeSubscriberLead: (registryId, subscriberId) =>
    client.patch(`/api/registries/${registryId}/subscribers/${subscriberId}/make-lead`).then((r) => r.data),
  teamActivity: (registryId) =>
    client.get(`/api/registries/${registryId}/team-activity`).then((r) => r.data),
  activity: (registryId) =>
    client.get(`/api/registries/${registryId}/activity`).then((r) => r.data),
  listMessages: (registryId) =>
    client.get(`/api/registries/${registryId}/messages`).then((r) => r.data),
  sendMessage: (registryId, data) =>
    client.post(`/api/registries/${registryId}/messages`, data).then((r) => r.data),
};

export const publicAPI = {
  getDiff: (token) => client.get(`/public/diff/${token}`).then((r) => r.data),
  getConversation: (token) => client.get(`/public/messages/${token}`).then((r) => r.data),
  sendConversationMessage: (token, data) =>
    client.post(`/public/messages/${token}`, data).then((r) => r.data),
};

export const adminAPI = {
  stats: () => client.get('/api/admin/stats').then((r) => r.data),
  users: () => client.get('/api/admin/users').then((r) => r.data),
  toggleUser: (userId) => client.post(`/api/admin/users/${userId}/toggle-active`).then((r) => r.data),
  makeAdmin: (userId) => client.post(`/api/admin/users/${userId}/make-admin`).then((r) => r.data),
  registries: () => client.get('/api/admin/registries').then((r) => r.data),
  registry: (registryId) => client.get(`/api/admin/registries/${registryId}`).then((r) => r.data),
};

export const profileAPI = {
  get: () => client.get('/api/me').then((r) => r.data),
  updateUsername: (data) => client.patch('/api/me/username', data).then((r) => r.data),
  updateEmail: (data) => client.patch('/api/me/email', data).then((r) => r.data),
  updatePassword: (data) => client.post('/api/me/password', data).then((r) => r.data),
};

export const agentAPI = {
  chat: (data) => client.post('/api/agent/chat', data).then((r) => r.data),
  stats: () => client.get('/api/dashboard/stats').then((r) => r.data),
};

/**
 * Versions API calls.
 * @typedef {{ id: string, version: string, status: string, schema_json: object, diff_result?: object, uploaded_at: string }} VersionResponse
 * @typedef {{ version: string, schema_json: object }} UploadVersionPayload
 */
export const versionsAPI = {
  /** @param {string} registryId @param {UploadVersionPayload} data @returns {Promise<VersionResponse>} */
  upload: (registryId, data) =>
    client.post(`/api/registries/${registryId}/versions`, data).then((r) => r.data),
  /** @param {string} registryId @returns {Promise<VersionResponse[]>} */
  list: (registryId) =>
    client.get(`/api/registries/${registryId}/versions`).then((r) => r.data),
};

/**
 * Diff API calls.
 */
export const diffAPI = {
  /** @param {string} registryId @param {string} fromId @param {string} toId */
  compare: (registryId, fromId, toId) =>
    client.get(`/api/diff/${registryId}?from=${fromId}&to=${toId}`).then((r) => r.data),
};

export default client;

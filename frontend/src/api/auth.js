import api from './axios'

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => api.post('/auth/login', { email, password }),
  refresh: (refresh_token) => api.post('/auth/refresh', { refresh_token }),
  getProfile: () => api.get('/auth/me'),
  updateProfile: (data) => api.put('/auth/me/update', data),
  changePassword: (old_password, new_password) =>
    api.post('/auth/change-password', { old_password, new_password }),
}
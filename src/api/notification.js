import api from './axios'

export const notificationAPI = {
  // Unified notifications (works for all roles)
  list: (params = {}) => api.get('/notifications', { params }),
  unreadCount: () => api.get('/notifications/unread-count'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),
  delete: (id) => api.delete(`/notifications/${id}/delete`),
  clearRead: () => api.delete('/notifications/clear-read'),
}
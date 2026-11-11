import api from './axios'

export const deliveryAPI = {
  // Availability
  getAvailability: () => api.get('/delivery/availability'),
  toggleAvailability: () => api.patch('/delivery/availability/toggle'),

  // Orders
  myOrders: (params = {}) => api.get('/delivery/orders', { params }),
  getOrder: (id) => api.get(`/delivery/orders/${id}`),
  history: (params = {}) => api.get('/delivery/history', { params }),

  // Actions
  pickup: (id) => api.patch(`/delivery/orders/${id}/pickup`),
  outForDelivery: (id) => api.patch(`/delivery/orders/${id}/out-for-delivery`),
  deliver: (id) => api.patch(`/delivery/orders/${id}/deliver`),

  // Location
  updateLocation: (order_id, lat, lng) =>
    api.post('/delivery/location', { order_id, lat, lng }),
  locationHistory: (orderId) => api.get(`/delivery/location/${orderId}/history`),

  // Notifications
  notifications: (params = {}) => api.get('/delivery/notifications', { params }),
  markRead: (id) => api.patch(`/delivery/notifications/${id}/read`),
}
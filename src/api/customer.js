import api from './axios'

export const customerAPI = {
  // Restaurants
  listRestaurants: (params = {}) => api.get('/restaurants', { params }),
  nearbyRestaurants: (lat, lng, radius = 5) =>
    api.get('/restaurants/nearby', { params: { lat, lng, radius } }),
  getRestaurant: (id) => api.get(`/restaurants/${id}`),
  getMenu: (id) => api.get(`/restaurants/${id}/menu`),
  getRestaurantReviews: (id) => api.get(`/restaurants/${id}/reviews`),

  // AI Recommendations
  aiRecommend: (query) => api.post('/customer/ai-recommend/', { query }),

  // Addresses
  listAddresses: () => api.get('/customer/addresses'),
  addAddress: (data) => api.post('/customer/addresses/add', data),
  updateAddress: (id, data) => api.put(`/customer/addresses/${id}/update`, data),
  deleteAddress: (id) => api.delete(`/customer/addresses/${id}/delete`),

  // Orders
  placeOrder: (data) => api.post('/orders/place', data),
  myOrders: (params = {}) => api.get('/orders', { params }),
  orderDetail: (id) => api.get(`/orders/${id}`),
  cancelOrder: (id, reason) => api.patch(`/orders/${id}/cancel`, { reason }),
  trackOrder: (id) => api.get(`/orders/${id}/track`),

  // Reviews
  submitReview: (order_id, rating, comment) =>
    api.post(`/orders/${order_id}/review`, { rating, comment }),
  myReviews: () => api.get('/reviews/me'),

  // Profile
  updateProfile: (data) => api.put('/auth/me/update', data),
  changePassword: (old_password, new_password) =>
    api.post('/auth/change-password', { old_password, new_password }),

  // Notifications
  getNotifications: (params = {}) => api.get('/notifications', { params }),
  unreadCount: () => api.get('/notifications/unread-count'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),
  deleteNotification: (id) => api.delete(`/notifications/${id}/delete`),
}
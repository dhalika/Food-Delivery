import api from './axios'

export const adminAPI = {
  // Dashboard
  stats: () => api.get('/admin/stats'),
  revenueReport: (from, to) => api.get(`/admin/revenue-report?from=${from}&to=${to}`),
  topRestaurants: (limit = 10) => api.get(`/admin/top-restaurants?limit=${limit}`),

  // Users
  listUsers: (params = {}) => api.get('/admin/users', { params }),
  getUser: (id) => api.get(`/admin/users/${id}`),
  blockUser: (id) => api.patch(`/admin/users/${id}/block`),
  deleteUser: (id) => api.delete(`/admin/users/${id}/delete`),

  // Restaurants
  listRestaurants: (params = {}) => api.get('/admin/restaurants', { params }),
  getRestaurant: (id) => api.get(`/admin/restaurants/${id}`),
  verifyRestaurant: (id) => api.patch(`/admin/restaurants/${id}/verify`),
  toggleRestaurant: (id) => api.patch(`/admin/restaurants/${id}/toggle-active`),
  deleteRestaurant: (id) => api.delete(`/admin/restaurants/${id}/delete`),

  // Orders
  listOrders: (params = {}) => api.get('/admin/orders', { params }),
  getOrder: (id) => api.get(`/admin/orders/${id}`),
  cancelOrder: (id, reason) => api.patch(`/admin/orders/${id}/cancel`, { reason }),

  // Coupons
  listCoupons: (params = {}) => api.get('/admin/coupons', { params }),
  createCoupon: (data) => api.post('/admin/coupons/create', data),
  updateCoupon: (id, data) => api.patch(`/admin/coupons/${id}`, data),
  toggleCoupon: (id) => api.patch(`/admin/coupons/${id}/toggle`),
  deleteCoupon: (id) => api.delete(`/admin/coupons/${id}/delete`),

  // Cache
  cacheStats: () => api.get('/admin/cache/stats'),
  clearCache: () => api.post('/admin/cache/clear-all'),
}
import api from './axios'

export const restaurantAPI = {
  // Profile
  create: (data) => api.post('/restaurants/create', data),
  myRestaurants: () => api.get('/restaurants/me'),
  update: (id, data) => api.put(`/restaurants/${id}/update`, data),
  toggleActive: (id) => api.patch(`/restaurants/${id}/toggle-active`),

  // Timings
  getTimings: (id) => api.get(`/restaurants/${id}/timings`),
  setTimings: (id, timings) => api.post(`/restaurants/${id}/timings/set`, { timings }),

  // Categories
  listCategories: (id) => api.get(`/restaurants/${id}/categories`),
  createCategory: (id, data) => api.post(`/restaurants/${id}/categories/create`, data),
  deleteCategory: (categoryId) => api.delete(`/categories/${categoryId}/delete`),

  // Menu Items
  listMenuItems: (id) => api.get(`/restaurants/${id}/menu-items`),
  createMenuItem: (id, data) => api.post(`/restaurants/${id}/menu-items/create`, data),
  updateMenuItem: (itemId, data) => api.put(`/menu-items/${itemId}/update`, data),
  toggleItemAvailability: (itemId) => api.patch(`/menu-items/${itemId}/toggle`),
  deleteMenuItem: (itemId) => api.delete(`/menu-items/${itemId}/delete`),

  // Orders
  listOrders: (params = {}) => api.get('/restaurant/orders', { params }),
  getOrder: (id) => api.get(`/restaurant/orders/${id}`),
  acceptOrder: (id, est_time = 30) => api.patch(`/restaurant/orders/${id}/accept`, { estimated_delivery_time: est_time }),
  markPreparing: (id) => api.patch(`/restaurant/orders/${id}/preparing`),
  rejectOrder: (id, reason) => api.patch(`/restaurant/orders/${id}/reject`, { reason }),

  // Dashboard
  dashboard: (restaurant_id) => api.get(`/restaurant/dashboard?restaurant_id=${restaurant_id}`),
  reviews: (id) => api.get(`/restaurant/${id}/reviews`),

  // Notifications
  notifications: (params = {}) => api.get('/restaurant/notifications', { params }),
  markRead: (id) => api.patch(`/restaurant/notifications/${id}/read`),
}
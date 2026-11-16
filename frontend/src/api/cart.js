import api from './axios'

export const cartAPI = {
  getCart: () => api.get('/cart'),
  addToCart: (menu_item_id, quantity = 1) => api.post('/cart/add', { menu_item_id, quantity }),
  updateItem: (item_id, quantity) => api.put(`/cart/items/${item_id}/update`, { quantity }),
  removeItem: (item_id) => api.delete(`/cart/items/${item_id}/remove`),
  clearCart: () => api.delete('/cart/clear'),
  applyCoupon: (code) => api.post('/cart/apply-coupon', { code }),
  availableCoupons: () => api.get('/coupons/available'),
}
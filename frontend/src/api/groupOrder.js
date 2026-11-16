import api from './axios'

export const groupOrderAPI = {
  create: (restaurant_id) => api.post('/group-orders/create', { restaurant_id }),
  getByCode: (code) => api.get(`/group-orders/code/${code}`),
  addItem: (group_id, menu_item_id, quantity = 1) =>
    api.post(`/group-orders/${group_id}/add-item`, { menu_item_id, quantity }),
  removeItem: (item_id) => api.delete(`/group-orders/items/${item_id}/remove`),
  finalize: (group_id, data) => api.post(`/group-orders/${group_id}/finalize`, data),
  cancel: (group_id) => api.post(`/group-orders/${group_id}/cancel`),
  myGroups: () => api.get('/group-orders/my'),
}
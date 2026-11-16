import api from './axios'

export const paymentAPI = {
  createOrder: (order_id) => api.post('/payments/create-order', { order_id }),
  verifyPayment: (data) => api.post('/payments/verify', data),
  markFailed: (order_id) => api.post('/payments/mark-failed', { order_id }),
  getStatus: (order_id) => api.get(`/payments/${order_id}/status`),
}
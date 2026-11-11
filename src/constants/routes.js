export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',

  CUSTOMER_HOME: '/customer',
  RESTAURANTS: '/customer/restaurants',
  RESTAURANT_DETAIL: (id) => `/customer/restaurants/${id}`,
  CART: '/customer/cart',
  CHECKOUT: '/customer/checkout',
  ORDER_TRACKING: (id) => `/customer/orders/${id}/track`,
  ORDER_HISTORY: '/customer/orders',
  PROFILE: '/customer/profile',

  RESTAURANT_DASHBOARD: '/restaurant/dashboard',
  RESTAURANT_MENU: '/restaurant/menu',
  RESTAURANT_ORDERS: '/restaurant/orders',

  DELIVERY_DASHBOARD: '/delivery/dashboard',
  DELIVERY_ORDERS: '/delivery/orders',

  ADMIN_DASHBOARD: '/admin/dashboard',
  ADMIN_USERS: '/admin/users',
  ADMIN_RESTAURANTS: '/admin/restaurants',
}
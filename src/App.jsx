import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'

// Auth
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import RoleSelect from './pages/auth/RoleSelect'
import ForgotPassword from './pages/auth/ForgotPassword'
import ProtectedRoute from './components/common/ProtectedRoute'

// Customer
import CustomerLayout from './layouts/CustomerLayout'
import Home from './pages/customer/Home'
import RestaurantList from './pages/customer/RestaurantList'
import RestaurantDetail from './pages/customer/RestaurantDetail'
import Cart from './pages/customer/Cart'
import Checkout from './pages/customer/Checkout'
import OrderPlaced from './pages/customer/OrderPlaced'
import Addresses from './pages/customer/Addresses'
import OrderHistory from './pages/customer/OrderHistory'
import OrderDetail from './pages/customer/OrderDetail'
import OrderTracking from './pages/customer/OrderTracking'
import ReviewOrder from './pages/customer/ReviewOrder'
import MyReviews from './pages/customer/MyReviews'
import Profile from './pages/customer/Profile'
import Notifications from './pages/customer/Notifications'
import GroupOrderManage from './pages/customer/GroupOrderManage'
import CreateGroupOrder from './pages/customer/CreateGroupOrder'

// Restaurant Owner
import RestaurantLayout from './layouts/RestaurantLayout'
import RestaurantDashboard from './pages/restaurant/Dashboard'
import IncomingOrders from './pages/restaurant/IncomingOrders'
import MenuManagement from './pages/restaurant/MenuManagement'
import Timings from './pages/restaurant/Timings'
import RestaurantProfile from './pages/restaurant/RestaurantProfile'

// Delivery Partner
import DeliveryLayout from './layouts/DeliveryLayout'
import DeliveryDashboard from './pages/delivery/Dashboard'
import AssignedOrders from './pages/delivery/AssignedOrders'
import DeliveryHistory from './pages/delivery/DeliveryHistory'
import DeliveryProfile from './pages/delivery/Profile'

// Admin
import AdminLayout from './layouts/AdminLayout'
import AdminDashboard from './pages/admin/Dashboard'
import AdminUsers from './pages/admin/Users'
import AdminRestaurants from './pages/admin/Restaurants'
import AdminOrders from './pages/admin/Orders'
import AdminCoupons from './pages/admin/Coupons'
import RevenueReport from './pages/admin/RevenueReport'
import CacheManagement from './pages/admin/CacheManagement'

function App() {
  const { isAuthenticated, user } = useAuthStore()

  const roleRedirect = () => {
    if (!isAuthenticated) return '/login'
    const routes = {
      customer: '/customer',
      restaurant_owner: '/restaurant/dashboard',
      delivery_partner: '/delivery/dashboard',
      admin: '/admin/dashboard',
    }
    return routes[user?.role] || '/login'
  }

  return (
    <div className="min-h-screen bg-cream">
      <Routes>
        <Route path="/" element={<Navigate to={roleRedirect()} replace />} />

        {/* AUTH */}
        <Route path="/login" element={isAuthenticated ? <Navigate to={roleRedirect()} /> : <Login />} />
        <Route path="/register" element={isAuthenticated ? <Navigate to={roleRedirect()} /> : <Register />} />
        <Route path="/role-select" element={isAuthenticated ? <Navigate to={roleRedirect()} /> : <RoleSelect />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />

        {/* CUSTOMER */}
        <Route path="/customer" element={
          <ProtectedRoute allowedRoles={['customer']}>
            <CustomerLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Home />} />
          <Route path="restaurants" element={<RestaurantList />} />
          <Route path="restaurants/:id" element={<RestaurantDetail />} />
          <Route path="cart" element={<Cart />} />
          <Route path="checkout" element={<Checkout />} />
          <Route path="addresses" element={<Addresses />} />
          <Route path="orders" element={<OrderHistory />} />
          <Route path="orders/:id" element={<OrderDetail />} />
          <Route path="orders/:id/success" element={<OrderPlaced />} />
          <Route path="orders/:id/track" element={<OrderTracking />} />
          <Route path="orders/:id/review" element={<ReviewOrder />} />
          <Route path="reviews" element={<MyReviews />} />
          <Route path="profile" element={<Profile />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="group/create" element={<CreateGroupOrder />} />
          <Route path="group/:code" element={<GroupOrderManage />} />
        </Route>

        {/* RESTAURANT OWNER */}
        <Route path="/restaurant" element={
          <ProtectedRoute allowedRoles={['restaurant_owner']}>
            <RestaurantLayout />
          </ProtectedRoute>
        }>
          <Route path="dashboard" element={<RestaurantDashboard />} />
          <Route path="orders" element={<IncomingOrders />} />
          <Route path="orders/:id" element={<PlaceholderPage title="Order Detail" />} />
          <Route path="menu" element={<MenuManagement />} />
          <Route path="timings" element={<Timings />} />
          <Route path="profile" element={<RestaurantProfile />} />
        </Route>

        {/* DELIVERY PARTNER */}
        <Route path="/delivery" element={
          <ProtectedRoute allowedRoles={['delivery_partner']}>
            <DeliveryLayout />
          </ProtectedRoute>
        }>
          <Route path="dashboard" element={<DeliveryDashboard />} />
          <Route path="orders" element={<AssignedOrders />} />
          <Route path="orders/:id" element={<PlaceholderPage title="Order Detail" />} />
          <Route path="history" element={<DeliveryHistory />} />
          <Route path="profile" element={<DeliveryProfile />} />
        </Route>

        {/* ADMIN */}
        <Route path="/admin" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminLayout />
          </ProtectedRoute>
        }>
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="restaurants" element={<AdminRestaurants />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="coupons" element={<AdminCoupons />} />
          <Route path="reports" element={<RevenueReport />} />
          <Route path="cache" element={<CacheManagement />} />
        </Route>

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>
  )
}

function PlaceholderPage({ title }) {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="card text-center max-w-md">
        <div className="text-5xl mb-4">🥡</div>
        <h1 className="text-2xl font-display font-bold mb-2">{title}</h1>
        <p className="text-muted mb-4">Coming soon!</p>
        <button onClick={() => { localStorage.clear(); window.location.href = '/login' }} className="btn-secondary">
          Logout
        </button>
      </div>
    </div>
  )
}

export default App
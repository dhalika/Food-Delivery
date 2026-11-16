import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../api/auth'
import toast from 'react-hot-toast'

export const useAuth = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated, setAuth, logout: clearAuth } = useAuthStore()

  const roleHomeRoute = (role) => {
    const routes = {
      customer: '/customer',
      restaurant_owner: '/restaurant/dashboard',
      delivery_partner: '/delivery/dashboard',
      admin: '/admin/dashboard',
    }
    return routes[role] || '/'
  }

  const login = async (email, password) => {
    try {
      const res = await authAPI.login(email, password)
      setAuth(res.user, res.access_token, res.refresh_token)
      toast.success(`Welcome back, ${res.user.name}!`)
      navigate(roleHomeRoute(res.user.role))
      return res
    } catch (err) {
      return null
    }
  }

  const register = async (data) => {
    try {
      const res = await authAPI.register(data)
      setAuth(res.user, res.access_token, res.refresh_token)
      toast.success(`Welcome to HongKong, ${res.user.name}! 🥡`)
      navigate(roleHomeRoute(res.user.role))
      return res
    } catch (err) {
      return null
    }
  }

  const logout = () => {
    clearAuth()
    toast.success('Logged out successfully')
    navigate('/login')
  }

  return { user, isAuthenticated, login, register, logout, roleHomeRoute }
}
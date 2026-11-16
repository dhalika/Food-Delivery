import axios from 'axios'
import toast from 'react-hot-toast'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { response, config } = error

    if (!response) {
      toast.error('Network error. Check your connection.')
      return Promise.reject(error)
    }

    const { status, data } = response

    if (status === 401 && !config._retry) {
      config._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', res.data.access_token)
          config.headers.Authorization = `Bearer ${res.data.access_token}`
          return api(config)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }

    if (status === 403) {
      toast.error(data.error || 'Access denied')
    } else if (status === 404) {
      toast.error(data.error || 'Not found')
    } else if (status >= 500) {
      toast.error('Server error. Please try again later.')
    } else if (data?.error) {
      toast.error(data.error)
    }

    return Promise.reject(error)
  }
)

export default api
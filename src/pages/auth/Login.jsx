import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthLayout from '../../layouts/AuthLayout'
import { useAuth } from '../../hooks/useAuth'
import { Mail, Lock, Eye, EyeOff, Loader2 } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    await login(form.email, form.password)
    setLoading(false)
  }

  return (
    <AuthLayout>
      <h1 className="text-3xl font-display mb-2">Welcome Back! 👋</h1>
      <p className="text-muted mb-8">Sign in to continue to HongKong</p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-semibold text-dark mb-2">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
              className="input-field pl-11"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-dark mb-2">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
            <input
              type={showPassword ? 'text' : 'password'}
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
              className="input-field pl-11 pr-11"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-dark"
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => navigate('/forgot-password')}
            className="text-sm text-brand-600 hover:underline font-semibold"
          >
            Forgot password?
          </button>
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading && <Loader2 className="animate-spin" size={20} />}
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-200"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-cream text-muted">New to HongKong?</span>
        </div>
      </div>

      <button onClick={() => navigate('/role-select')} className="btn-secondary w-full">
        Create an Account
      </button>
    </AuthLayout>
  )
}
import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import AuthLayout from '../../layouts/AuthLayout'
import { useAuth } from '../../hooks/useAuth'
import { User, Mail, Phone, Lock, Eye, EyeOff, Loader2, ArrowLeft } from 'lucide-react'

export default function Register() {
  const navigate = useNavigate()
  const location = useLocation()
  const { register } = useAuth()
  const defaultRole = location.state?.role || 'customer'

  const [form, setForm] = useState({
    name: '', email: '', phone: '', password: '', role: defaultRole,
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const roleLabels = {
    customer: 'Customer',
    restaurant_owner: 'Restaurant Owner',
    delivery_partner: 'Delivery Partner',
    admin: 'Admin',
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password.length < 8) {
      return
    }
    setLoading(true)
    await register(form)
    setLoading(false)
  }

  return (
    <AuthLayout>
      <button onClick={() => navigate('/role-select')} className="flex items-center gap-1 text-muted hover:text-dark mb-6">
        <ArrowLeft size={18} /> Change role
      </button>

      <div className="inline-block bg-brand-100 border border-brand-300 text-brand-700 px-3 py-1 rounded-full text-xs font-semibold mb-3">
        Signing up as {roleLabels[form.role]}
      </div>
      <h1 className="text-3xl font-display mb-2">Create Account 🥡</h1>
      <p className="text-muted mb-6">Join HongKong in just a few seconds</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField icon={<User size={20} />} type="text" placeholder="Full Name" value={form.name}
          onChange={(v) => setForm({ ...form, name: v })} />

        <InputField icon={<Mail size={20} />} type="email" placeholder="Email address" value={form.email}
          onChange={(v) => setForm({ ...form, email: v })} />

        <InputField icon={<Phone size={20} />} type="tel" placeholder="Phone (10 digits)" value={form.phone}
          onChange={(v) => setForm({ ...form, phone: v })} maxLength={15} />

        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
          <input
            type={showPassword ? 'text' : 'password'}
            required
            minLength={8}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            placeholder="Password (min 8 chars)"
            className="input-field pl-11 pr-11"
          />
          <button type="button" onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted">
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        </div>

        <p className="text-xs text-muted">
          By signing up, you agree to our Terms & Privacy Policy
        </p>

        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
          {loading && <Loader2 className="animate-spin" size={20} />}
          {loading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>

      <p className="text-center text-sm text-muted mt-6">
        Already have an account?{' '}
        <button onClick={() => navigate('/login')} className="text-brand-600 font-semibold hover:underline">
          Sign In
        </button>
      </p>
    </AuthLayout>
  )
}

function InputField({ icon, type, placeholder, value, onChange, maxLength }) {
  return (
    <div className="relative">
      <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted">{icon}</div>
      <input
        type={type}
        required
        maxLength={maxLength}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="input-field pl-11"
      />
    </div>
  )
}
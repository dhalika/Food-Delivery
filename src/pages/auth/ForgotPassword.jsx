import { useNavigate } from 'react-router-dom'
import AuthLayout from '../../layouts/AuthLayout'
import { Mail, ArrowLeft } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    toast.success('If this email exists, reset link sent!')
    setTimeout(() => navigate('/login'), 2000)
  }

  return (
    <AuthLayout>
      <button onClick={() => navigate('/login')} className="flex items-center gap-1 text-muted hover:text-dark mb-6">
        <ArrowLeft size={18} /> Back to login
      </button>

      <h1 className="text-3xl font-display mb-2">Forgot Password? 🔐</h1>
      <p className="text-muted mb-8">Enter your email and we'll send reset instructions</p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="input-field pl-11"
          />
        </div>

        <button type="submit" className="btn-primary w-full">
          Send Reset Link
        </button>
      </form>
    </AuthLayout>
  )
}
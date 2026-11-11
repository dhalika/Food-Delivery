import { useNavigate } from 'react-router-dom'
import AuthLayout from '../../layouts/AuthLayout'
import { User, Store, Truck, Shield, ChevronRight } from 'lucide-react'

export default function RoleSelect() {
  const navigate = useNavigate()

  const roles = [
    { id: 'customer', name: 'Customer', desc: 'Order food from restaurants', icon: <User />, color: 'from-blue-50 to-blue-100' },
    { id: 'restaurant_owner', name: 'Restaurant Owner', desc: 'Manage your restaurant', icon: <Store />, color: 'from-green-50 to-green-100' },
    { id: 'delivery_partner', name: 'Delivery Partner', desc: 'Earn by delivering orders', icon: <Truck />, color: 'from-orange-50 to-orange-100' },
    { id: 'admin', name: 'Admin', desc: 'Manage the platform', icon: <Shield />, color: 'from-purple-50 to-purple-100' },
  ]

  const handleSelect = (roleId) => {
    navigate('/register', { state: { role: roleId } })
  }

  return (
    <AuthLayout>
      <h1 className="text-3xl font-display mb-2">Join HongKong 🥡</h1>
      <p className="text-muted mb-8">Choose your role to get started</p>

      <div className="space-y-3">
        {roles.map((role) => (
          <button
            key={role.id}
            onClick={() => handleSelect(role.id)}
            className={`w-full p-4 bg-gradient-to-r ${role.color} rounded-xl border-2 border-transparent hover:border-brand-500 transition-all flex items-center justify-between group`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-dark">
                {role.icon}
              </div>
              <div className="text-left">
                <h3 className="font-semibold text-dark">{role.name}</h3>
                <p className="text-xs text-muted">{role.desc}</p>
              </div>
            </div>
            <ChevronRight className="text-muted group-hover:text-brand-600 transition" />
          </button>
        ))}
      </div>

      <p className="text-center text-sm text-muted mt-8">
        Already have an account?{' '}
        <button onClick={() => navigate('/login')} className="text-brand-600 font-semibold hover:underline">
          Sign In
        </button>
      </p>
    </AuthLayout>
  )
}
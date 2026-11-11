import { Outlet, useNavigate, Link } from 'react-router-dom'
import { useEffect } from 'react'
import { ShoppingCart, User, MapPin, Package, LogOut, Bell } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useCart } from '../hooks/useCart'
import { useCartStore } from '../store/cartStore'
import Logo from '../components/common/Logo'
import AIChat from '../components/AIChat'

export default function CustomerLayout() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { refreshCart } = useCart()
  const { itemCount } = useCartStore()

  useEffect(() => { refreshCart() }, [])

  return (
    <div className="min-h-screen bg-cream">
      <header className="bg-white shadow-card sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div onClick={() => navigate('/customer')} className="cursor-pointer">
            <Logo size="small" />
          </div>

          <div className="hidden md:flex items-center gap-2 bg-cream px-4 py-2 rounded-xl">
            <MapPin size={18} className="text-brand-600" />
            <span className="text-sm text-dark font-semibold">Hyderabad</span>
          </div>

          <div className="flex items-center gap-2">
            <NavIcon icon={<Bell />} onClick={() => navigate('/customer/notifications')} />
            <NavIcon icon={<Package />} onClick={() => navigate('/customer/orders')} />
            <NavIcon
              icon={<ShoppingCart />}
              onClick={() => navigate('/customer/cart')}
              badge={itemCount > 0 ? itemCount : null}
            />

            <div className="relative group">
              <NavIcon icon={<User />} />
              <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                <div className="p-3 border-b">
                  <p className="font-semibold">{user?.name}</p>
                  <p className="text-xs text-muted">{user?.email}</p>
                </div>
                <Link to="/customer/profile" className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-cream">
                  <User size={16} /> Profile
                </Link>
                <Link to="/customer/addresses" className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-cream">
                  <MapPin size={16} /> Addresses
                </Link>
                <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-red-50 text-red-600">
                  <LogOut size={16} /> Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      {/* AI Food Assistant - Floating Chat */}
      <AIChat />
    </div>
  )
}

function NavIcon({ icon, onClick, badge }) {
  return (
    <button onClick={onClick} className="relative p-2 hover:bg-cream rounded-lg transition">
      {icon}
      {badge !== null && badge !== undefined && (
        <span className="absolute -top-1 -right-1 bg-danger text-white text-xs rounded-full min-w-5 h-5 flex items-center justify-center px-1 font-bold">
          {badge}
        </span>
      )}
    </button>
  )
}
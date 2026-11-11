import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, ShoppingBag, Menu as MenuIcon, Store, LogOut, Bell, User, Clock } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import Logo from '../components/common/Logo'

export default function RestaurantLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const menu = [
    { path: '/restaurant/dashboard', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { path: '/restaurant/orders', icon: <ShoppingBag size={20} />, label: 'Orders' },
    { path: '/restaurant/menu', icon: <MenuIcon size={20} />, label: 'Menu' },
    { path: '/restaurant/timings', icon: <Clock size={20} />, label: 'Timings' },
    { path: '/restaurant/profile', icon: <Store size={20} />, label: 'Restaurant' },
  ]

  return (
    <div className="min-h-screen bg-cream flex">
      {/* SIDEBAR */}
      <aside className="w-64 bg-white shadow-card flex flex-col sticky top-0 h-screen">
        <div className="p-6 border-b">
          <Logo size="small" />
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {menu.map((item) => {
            const active = location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition ${
                  active ? 'bg-brand-500 text-dark shadow-brand' : 'text-muted hover:bg-cream'
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-brand-400 rounded-full flex items-center justify-center font-bold">
              {user?.name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm truncate">{user?.name}</p>
              <p className="text-xs text-muted truncate">{user?.email}</p>
            </div>
          </div>
          <button onClick={logout} className="w-full flex items-center justify-center gap-2 py-2 text-danger hover:bg-red-50 rounded-lg font-semibold text-sm">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="flex-1 p-8 overflow-x-hidden">
        <Outlet />
      </main>
    </div>
  )
}
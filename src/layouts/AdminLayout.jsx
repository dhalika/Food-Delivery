import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, Store, ShoppingBag, Tag, TrendingUp, LogOut, Database } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import Logo from '../components/common/Logo'

export default function AdminLayout() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const menu = [
    { path: '/admin/dashboard', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { path: '/admin/users', icon: <Users size={20} />, label: 'Users' },
    { path: '/admin/restaurants', icon: <Store size={20} />, label: 'Restaurants' },
    { path: '/admin/orders', icon: <ShoppingBag size={20} />, label: 'Orders' },
    { path: '/admin/coupons', icon: <Tag size={20} />, label: 'Coupons' },
    { path: '/admin/reports', icon: <TrendingUp size={20} />, label: 'Reports' },
    { path: '/admin/cache', icon: <Database size={20} />, label: 'Cache' },
  ]

  return (
    <div className="min-h-screen bg-cream flex">
      <aside className="w-64 bg-dark text-white flex flex-col sticky top-0 h-screen">
        <div className="p-6 border-b border-white/10">
          <Logo size="small" />
          <p className="text-xs text-brand-500 font-bold mt-2">ADMIN PANEL</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {menu.map((item) => {
            const active = location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition ${
                  active ? 'bg-brand-500 text-dark shadow-brand' : 'text-gray-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-brand-500 rounded-full flex items-center justify-center font-bold text-dark">
              👑
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm truncate">{user?.name}</p>
              <p className="text-xs text-gray-400">Admin</p>
            </div>
          </div>
          <button onClick={logout} className="w-full flex items-center justify-center gap-2 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg font-semibold text-sm">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-x-hidden">
        <Outlet />
      </main>
    </div>
  )
}
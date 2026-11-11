import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { LayoutDashboard, Package, History, User, LogOut, Power } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { deliveryAPI } from '../api/delivery'
import Logo from '../components/common/Logo'
import toast from 'react-hot-toast'

export default function DeliveryLayout() {
  const location = useLocation()
  const { user, logout } = useAuth()
  const [available, setAvailable] = useState(false)

  useEffect(() => { loadStatus() }, [])

  const loadStatus = async () => {
    try {
      const res = await deliveryAPI.getAvailability()
      setAvailable(res.is_available)
    } catch {}
  }

  const handleToggle = async () => {
    try {
      const res = await deliveryAPI.toggleAvailability()
      setAvailable(res.is_available)
      toast.success(res.is_available ? '🟢 You are ONLINE' : '🔴 You are OFFLINE')
    } catch {}
  }

  const menu = [
    { path: '/delivery/dashboard', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { path: '/delivery/orders', icon: <Package size={20} />, label: 'Active Orders' },
    { path: '/delivery/history', icon: <History size={20} />, label: 'History' },
    { path: '/delivery/profile', icon: <User size={20} />, label: 'Profile' },
  ]

  return (
    <div className="min-h-screen bg-cream flex">
      <aside className="w-64 bg-white shadow-card flex flex-col sticky top-0 h-screen">
        <div className="p-6 border-b">
          <Logo size="small" />
        </div>

        {/* Online/Offline Toggle */}
        <div className="p-4 border-b">
          <button
            onClick={handleToggle}
            className={`w-full p-3 rounded-xl flex items-center justify-between font-semibold transition ${
              available ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
            }`}
          >
            <div className="flex items-center gap-2">
              <Power size={18} />
              <span>{available ? 'Online' : 'Offline'}</span>
            </div>
            <div className={`w-3 h-3 rounded-full ${available ? 'bg-success animate-pulse' : 'bg-danger'}`}></div>
          </button>
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
              🛵
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm truncate">{user?.name}</p>
              <p className="text-xs text-muted truncate">Delivery Partner</p>
            </div>
          </div>
          <button onClick={logout} className="w-full flex items-center justify-center gap-2 py-2 text-danger hover:bg-red-50 rounded-lg font-semibold text-sm">
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
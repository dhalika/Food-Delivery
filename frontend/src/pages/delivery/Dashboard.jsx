import { useEffect, useState } from 'react'
import { deliveryAPI } from '../../api/delivery'
import { Loader2, Package, DollarSign, TrendingUp, Clock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function DeliveryDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [activeOrders, setActiveOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    load()
    const timer = setInterval(load, 15000)
    return () => clearInterval(timer)
  }, [])

  const load = async () => {
    try {
      const [h, o] = await Promise.all([
        deliveryAPI.history(),
        deliveryAPI.myOrders(),
      ])
      setStats(h.stats)
      setActiveOrders(o.orders || [])
    } finally { setLoading(false) }
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">Delivery Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Today's Deliveries" value={stats?.today_deliveries || 0} icon={<Package />} color="bg-brand-100 text-brand-700" />
        <StatCard title="Today's Earnings" value={`₹${stats?.today_revenue_handled || 0}`} icon={<DollarSign />} color="bg-success/20 text-success" />
        <StatCard title="Total Deliveries" value={stats?.total_deliveries || 0} icon={<TrendingUp />} color="bg-info/20 text-info" />
        <StatCard title="Active Orders" value={activeOrders.length} icon={<Clock />} color="bg-warning/20 text-warning" />
      </div>

      {/* Active Orders */}
      <div>
        <h2 className="text-xl font-display font-bold mb-3">🚨 Active Orders</h2>
        {activeOrders.length === 0 ? (
          <div className="card text-center py-8">
            <Package size={40} className="mx-auto text-muted mb-2" />
            <p className="text-muted">No active orders. Wait for new assignments!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeOrders.map((o) => (
              <div key={o.id} onClick={() => navigate(`/delivery/orders/${o.id}`)}
                className="card cursor-pointer hover:shadow-brand">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-bold">#{o.id.slice(0, 8).toUpperCase()}</p>
                    <p className="text-sm text-muted">{o.restaurant?.name} → {o.customer?.name}</p>
                    <p className="text-xs text-muted mt-1">{o.restaurant?.address}</p>
                  </div>
                  <div className="text-right">
                    <StatusBadge status={o.status} />
                    <p className="font-bold mt-2">₹{o.final_amount}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color }) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted">{title}</p>
          <p className="text-3xl font-display font-extrabold mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-xl ${color}`}>{icon}</div>
      </div>
    </div>
  )
}

function StatusBadge({ status }) {
  const config = {
    accepted: 'bg-brand-200 text-brand-700',
    preparing: 'bg-warning/20 text-warning',
    picked_up: 'bg-info/20 text-info',
    out_for_delivery: 'bg-info/20 text-info',
  }
  return <span className={`px-2 py-1 rounded-lg text-xs font-bold ${config[status] || 'bg-muted/20'}`}>{status?.replace('_', ' ').toUpperCase()}</span>
}
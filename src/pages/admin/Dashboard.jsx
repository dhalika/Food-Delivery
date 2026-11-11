import { useEffect, useState } from 'react'
import { adminAPI } from '../../api/admin'
import { Users, Store, ShoppingBag, DollarSign, TrendingUp, AlertCircle, Loader2 } from 'lucide-react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS = ['#FFC72C', '#22C55E', '#3B82F6', '#EF4444', '#F59E0B', '#8B5CF6', '#EC4899']

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [top, setTop] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const [s, t] = await Promise.all([
        adminAPI.stats(),
        adminAPI.topRestaurants(5),
      ])
      setStats(s)
      setTop(t.top_restaurants || [])
    } finally { setLoading(false) }
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>

  const statusData = Object.entries(stats?.orders_by_status || {}).map(([name, value]) => ({ name, value }))
  const roleData = Object.entries(stats?.users_by_role || {}).map(([name, value]) => ({ name: name.replace('_', ' '), value }))

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">Admin Dashboard</h1>

      {/* Big Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Orders" value={stats?.total_orders} subtitle={`+${stats?.today_orders} today`} icon={<ShoppingBag />} color="bg-brand-100 text-brand-700" />
        <StatCard title="Total Revenue" value={`₹${stats?.total_revenue?.toLocaleString()}`} subtitle={`₹${stats?.today_revenue} today`} icon={<DollarSign />} color="bg-success/20 text-success" />
        <StatCard title="Active Users" value={stats?.active_users} subtitle="All roles" icon={<Users />} color="bg-info/20 text-info" />
        <StatCard title="Active Restaurants" value={stats?.active_restaurants} subtitle={`${stats?.pending_verifications} pending`} icon={<Store />} color="bg-warning/20 text-warning" />
      </div>

      {/* Alerts */}
      {stats?.pending_verifications > 0 && (
        <div className="card bg-warning/10 border border-warning/30 flex items-center gap-3">
          <AlertCircle className="text-warning" />
          <div>
            <p className="font-bold">{stats.pending_verifications} restaurants waiting for verification</p>
            <p className="text-sm text-muted">Review them in Restaurants section</p>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Orders by Status */}
        <div className="card">
          <h3 className="font-bold text-lg mb-4">📦 Orders by Status</h3>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-center text-muted py-8">No data</p>}
        </div>

        {/* Users by Role */}
        <div className="card">
          <h3 className="font-bold text-lg mb-4">👥 Users by Role</h3>
          {roleData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={roleData}>
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="value" fill="#FFC72C" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-center text-muted py-8">No data</p>}
        </div>
      </div>

      {/* Top Restaurants */}
      <div className="card">
        <h3 className="font-bold text-lg mb-4">🏆 Top Restaurants (Last 30 Days)</h3>
        {top.length === 0 ? (
          <p className="text-muted text-center py-6">No data</p>
        ) : (
          <div className="space-y-2">
            {top.map((r, i) => (
              <div key={r.restaurant_id} className="flex items-center gap-3 p-3 bg-cream rounded-xl">
                <div className="w-10 h-10 bg-brand-500 rounded-full flex items-center justify-center font-bold text-dark">
                  #{i + 1}
                </div>
                <div className="flex-1">
                  <p className="font-bold">{r.name}</p>
                  <p className="text-xs text-muted">{r.city} • ⭐ {r.avg_rating}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">₹{r.total_revenue?.toLocaleString()}</p>
                  <p className="text-xs text-muted">{r.total_orders} orders</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Avg Order Value */}
      <div className="card bg-gradient-to-r from-brand-400 to-brand-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold">Average Order Value</p>
            <p className="text-4xl font-display font-extrabold mt-1">₹{stats?.avg_order_value}</p>
          </div>
          <TrendingUp size={48} />
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, subtitle, icon, color }) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted">{title}</p>
          <p className="text-3xl font-display font-extrabold mt-1">{value || 0}</p>
          <p className="text-xs text-success mt-1 font-semibold">{subtitle}</p>
        </div>
        <div className={`p-3 rounded-xl ${color}`}>{icon}</div>
      </div>
    </div>
  )
}
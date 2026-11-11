import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { restaurantAPI } from '../../api/restaurant'
import { useRestaurantStore } from '../../store/restaurantStore'
import { TrendingUp, Package, Clock, Star, Loader2, Store, Plus } from 'lucide-react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function Dashboard() {
  const navigate = useNavigate()
  const { selectedRestaurant, setRestaurant } = useRestaurantStore()
  const [restaurants, setRestaurants] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadRestaurants() }, [])
  useEffect(() => { if (selectedRestaurant) loadStats() }, [selectedRestaurant])

  const loadRestaurants = async () => {
    try {
      const res = await restaurantAPI.myRestaurants()
      setRestaurants(res.restaurants || [])
      if (res.restaurants?.[0] && !selectedRestaurant) {
        setRestaurant(res.restaurants[0])
      }
    } finally { setLoading(false) }
  }

  const loadStats = async () => {
    try {
      const res = await restaurantAPI.dashboard(selectedRestaurant.id)
      setStats(res)
    } catch {}
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>

  if (restaurants.length === 0) {
    return (
      <div className="card text-center py-16 max-w-md mx-auto">
        <Store size={60} className="mx-auto text-muted mb-4" />
        <h2 className="text-2xl font-display font-bold mb-2">Welcome to HongKong!</h2>
        <p className="text-muted mb-6">Create your restaurant to get started</p>
        <button onClick={() => navigate('/restaurant/profile/create')} className="btn-primary flex items-center gap-2 mx-auto">
          <Plus size={18} /> Create Restaurant
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-display font-bold">Dashboard</h1>
          <p className="text-muted mt-1">{selectedRestaurant?.name}</p>
        </div>
        <select
          value={selectedRestaurant?.id || ''}
          onChange={(e) => setRestaurant(restaurants.find(r => r.id === e.target.value))}
          className="input-field w-auto"
        >
          {restaurants.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
      </div>

      {/* Verification Status */}
      {!selectedRestaurant?.is_verified && (
        <div className="card bg-warning/10 border border-warning/30 flex items-center gap-3">
          <Clock className="text-warning" />
          <p className="text-sm">Your restaurant is pending admin verification.</p>
        </div>
      )}

      {/* Stats Grid */}
      {stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard title="Today's Orders" value={stats.today?.orders} subtitle={`₹${stats.today?.revenue}`} icon={<Package />} color="bg-brand-100 text-brand-700" />
            <StatCard title="This Week" value={stats.this_week?.orders} subtitle={`₹${stats.this_week?.revenue}`} icon={<TrendingUp />} color="bg-success/20 text-success" />
            <StatCard title="This Month" value={stats.this_month?.orders} subtitle={`₹${stats.this_month?.revenue}`} icon={<TrendingUp />} color="bg-info/20 text-info" />
            <StatCard title="Lifetime" value={stats.lifetime?.orders} subtitle={`₹${stats.lifetime?.revenue}`} icon={<Star />} color="bg-warning/20 text-warning" />
          </div>

          {/* Revenue Chart */}
          <div className="card">
            <h3 className="font-bold text-lg mb-4">📈 Revenue (Last 7 Days)</h3>
            {stats.daily_revenue_last_7_days?.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={stats.daily_revenue_last_7_days}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" stroke="#6B7280" fontSize={12} />
                  <YAxis stroke="#6B7280" fontSize={12} />
                  <Tooltip />
                  <Line type="monotone" dataKey="revenue" stroke="#FFC72C" strokeWidth={3} dot={{ fill: '#FFC72C', r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-muted text-center py-8">No data yet</p>
            )}
          </div>

          {/* Top Items */}
          <div className="card">
            <h3 className="font-bold text-lg mb-4">🔥 Top Selling Items</h3>
            {stats.top_selling_items?.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.top_selling_items.slice(0, 5)} layout="vertical">
                  <XAxis type="number" stroke="#6B7280" fontSize={12} />
                  <YAxis dataKey="name" type="category" stroke="#6B7280" fontSize={12} width={120} />
                  <Tooltip />
                  <Bar dataKey="quantity_sold" fill="#FFC72C" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-muted text-center py-8">No sales data yet</p>
            )}
          </div>

          {/* Orders by Status */}
          <div className="card">
            <h3 className="font-bold text-lg mb-4">📦 Orders by Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(stats.orders_by_status || {}).map(([status, count]) => (
                <div key={status} className="bg-cream rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-xs text-muted capitalize">{status.replace('_', ' ')}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
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
          <p className="text-sm font-semibold text-success mt-1">{subtitle}</p>
        </div>
        <div className={`p-3 rounded-xl ${color}`}>{icon}</div>
      </div>
    </div>
  )
}
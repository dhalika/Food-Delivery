import { useEffect, useState } from 'react'
import { deliveryAPI } from '../../api/delivery'
import { Loader2, CheckCircle } from 'lucide-react'
import { format } from 'date-fns'

export default function DeliveryHistory() {
  const [data, setData] = useState({ stats: null, deliveries: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    deliveryAPI.history().then((res) => {
      setData({ stats: res.stats, deliveries: res.deliveries || [] })
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">Delivery History</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Total Deliveries" value={data.stats?.total_deliveries || 0} />
        <StatCard title="Total Revenue" value={`₹${data.stats?.total_revenue_handled || 0}`} />
        <StatCard title="Today" value={data.stats?.today_deliveries || 0} />
        <StatCard title="Today Revenue" value={`₹${data.stats?.today_revenue_handled || 0}`} />
      </div>

      {data.deliveries.length === 0 ? (
        <div className="card text-center py-12">
          <CheckCircle size={48} className="mx-auto text-muted mb-3" />
          <p className="text-muted">No completed deliveries yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {data.deliveries.map((d) => (
            <div key={d.order_id} className="card flex justify-between items-center">
              <div>
                <p className="font-bold">#{d.order_id.slice(0, 8).toUpperCase()}</p>
                <p className="text-sm text-muted">{d.restaurant_name}</p>
                <p className="text-xs text-muted">{format(new Date(d.delivered_at), 'MMM d, h:mm a')}</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-success">+₹{d.amount}</p>
                <CheckCircle size={16} className="text-success inline" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value }) {
  return (
    <div className="card">
      <p className="text-xs text-muted">{title}</p>
      <p className="text-2xl font-display font-extrabold mt-1">{value}</p>
    </div>
  )
}
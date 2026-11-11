import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import { Loader2, Package, Clock, CheckCircle, XCircle } from 'lucide-react'
import { format } from 'date-fns'

const STATUS_CONFIG = {
  placed: { label: 'Placed', color: 'bg-info/20 text-info', icon: <Clock size={14} /> },
  accepted: { label: 'Accepted', color: 'bg-info/20 text-info', icon: <CheckCircle size={14} /> },
  preparing: { label: 'Preparing', color: 'bg-warning/20 text-warning', icon: <Clock size={14} /> },
  picked_up: { label: 'Picked Up', color: 'bg-warning/20 text-warning', icon: <Package size={14} /> },
  out_for_delivery: { label: 'On the Way', color: 'bg-warning/20 text-warning', icon: <Package size={14} /> },
  delivered: { label: 'Delivered', color: 'bg-success/20 text-success', icon: <CheckCircle size={14} /> },
  cancelled: { label: 'Cancelled', color: 'bg-danger/20 text-danger', icon: <XCircle size={14} /> },
}

export default function OrderHistory() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => { load() }, [filter])

  const load = async () => {
    setLoading(true)
    try {
      const params = filter ? { status: filter } : {}
      const res = await customerAPI.myOrders(params)
      setOrders(res.orders || [])
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">My Orders</h1>

      {/* Filter chips */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <Chip label="All" active={!filter} onClick={() => setFilter('')} />
        <Chip label="Active" active={filter === 'placed'} onClick={() => setFilter('placed')} />
        <Chip label="Delivered" active={filter === 'delivered'} onClick={() => setFilter('delivered')} />
        <Chip label="Cancelled" active={filter === 'cancelled'} onClick={() => setFilter('cancelled')} />
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>
      ) : orders.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-6xl mb-3">📦</div>
          <h3 className="text-xl font-bold mb-1">No orders yet</h3>
          <p className="text-muted mb-4">Start exploring restaurants!</p>
          <button onClick={() => navigate('/customer')} className="btn-primary">Browse Restaurants</button>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => {
            const status = STATUS_CONFIG[order.status] || STATUS_CONFIG.placed
            return (
              <div key={order.id} onClick={() => navigate(`/customer/orders/${order.id}`)}
                className="card cursor-pointer hover:shadow-brand transition-all">
                <div className="flex justify-between items-start">
                  <div className="flex gap-4 flex-1">
                    {order.restaurant_logo ? (
                      <img src={order.restaurant_logo} alt="" className="w-16 h-16 rounded-xl object-cover" />
                    ) : (
                      <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-brand-200 to-brand-400 flex items-center justify-center text-2xl">🍽️</div>
                    )}
                    <div className="flex-1">
                      <h4 className="font-bold">{order.restaurant_name}</h4>
                      <p className="text-xs text-muted">Order #{order.id.slice(0, 8).toUpperCase()}</p>
                      <p className="text-xs text-muted">{order.item_count} items • {format(new Date(order.placed_at), 'MMM d, h:mm a')}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold ${status.color}`}>
                      {status.icon} {status.label}
                    </div>
                    <p className="font-bold mt-2">₹{order.final_amount}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function Chip({ label, active, onClick }) {
  return (
    <button onClick={onClick} className={`px-5 py-2 rounded-full whitespace-nowrap font-semibold text-sm ${active ? 'bg-brand-500 text-dark shadow-brand' : 'bg-white text-muted border border-gray-200'}`}>
      {label}
    </button>
  )
}
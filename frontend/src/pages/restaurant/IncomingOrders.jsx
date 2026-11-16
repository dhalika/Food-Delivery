import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { restaurantAPI } from '../../api/restaurant'
import { Loader2, Clock, CheckCircle, XCircle, Package, Phone } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function IncomingOrders() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    load()
    // Auto-refresh every 10 seconds
    const timer = setInterval(load, 10000)
    return () => clearInterval(timer)
  }, [filter])

  const load = async () => {
    try {
      const params = filter ? { status: filter } : {}
      const res = await restaurantAPI.listOrders(params)
      setOrders(res.orders || [])
    } finally { setLoading(false) }
  }

  const handleAccept = async (id) => {
    const time = prompt('Estimated delivery time (minutes)?', '30')
    if (!time) return
    try {
      await restaurantAPI.acceptOrder(id, parseInt(time))
      toast.success('Order accepted!')
      load()
    } catch {}
  }

  const handleReject = async (id) => {
    const reason = prompt('Reason for rejecting?')
    if (!reason) return
    try {
      await restaurantAPI.rejectOrder(id, reason)
      toast.success('Order rejected')
      load()
    } catch {}
  }

  const handlePreparing = async (id) => {
    try {
      await restaurantAPI.markPreparing(id)
      toast.success('Marked as preparing')
      load()
    } catch {}
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-display font-bold">Incoming Orders</h1>
        <button onClick={load} className="btn-secondary text-sm">Refresh</button>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        <Chip label="All" active={!filter} onClick={() => setFilter('')} />
        <Chip label="Placed" active={filter === 'placed'} onClick={() => setFilter('placed')} />
        <Chip label="Accepted" active={filter === 'accepted'} onClick={() => setFilter('accepted')} />
        <Chip label="Preparing" active={filter === 'preparing'} onClick={() => setFilter('preparing')} />
        <Chip label="Delivered" active={filter === 'delivered'} onClick={() => setFilter('delivered')} />
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>
      ) : orders.length === 0 ? (
        <div className="card text-center py-12">
          <Package size={48} className="mx-auto text-muted mb-3" />
          <h3 className="text-xl font-bold mb-1">No orders</h3>
          <p className="text-muted">New orders will appear here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((o) => (
            <div key={o.id} className="card">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <p className="font-bold">Order #{o.id.slice(0, 8).toUpperCase()}</p>
                  <p className="text-xs text-muted">{format(new Date(o.placed_at), 'MMM d, h:mm a')}</p>
                </div>
                <StatusBadge status={o.status} />
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                <div>
                  <p className="text-muted text-xs">Customer</p>
                  <p className="font-semibold">{o.customer_name}</p>
                  <a href={`tel:${o.customer_phone}`} className="text-xs text-brand-600 flex items-center gap-1">
                    <Phone size={12} /> {o.customer_phone}
                  </a>
                </div>
                <div>
                  <p className="text-muted text-xs">Amount</p>
                  <p className="font-bold text-lg">₹{o.final_amount}</p>
                  <p className="text-xs text-muted">{o.item_count} items • {o.payment_method?.toUpperCase()}</p>
                </div>
              </div>

              {o.special_instructions && (
                <div className="bg-warning/10 border border-warning/30 rounded-lg p-2 mb-3 text-xs">
                  <b>📝 Note:</b> {o.special_instructions}
                </div>
              )}

              <div className="flex gap-2">
                <button onClick={() => navigate(`/restaurant/orders/${o.id}`)} className="btn-secondary text-sm flex-1">
                  View Details
                </button>
                {o.status === 'placed' && (
                  <>
                    <button onClick={() => handleAccept(o.id)} className="btn-primary text-sm flex-1 flex items-center justify-center gap-1">
                      <CheckCircle size={14} /> Accept
                    </button>
                    <button onClick={() => handleReject(o.id)} className="text-sm px-4 py-2 bg-red-50 text-danger rounded-xl font-semibold flex items-center gap-1">
                      <XCircle size={14} /> Reject
                    </button>
                  </>
                )}
                {o.status === 'accepted' && (
                  <button onClick={() => handlePreparing(o.id)} className="btn-primary text-sm flex-1 flex items-center justify-center gap-1">
                    <Clock size={14} /> Mark Preparing
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Chip({ label, active, onClick }) {
  return (
    <button onClick={onClick} className={`px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap ${active ? 'bg-brand-500 text-dark' : 'bg-white text-muted border'}`}>
      {label}
    </button>
  )
}

function StatusBadge({ status }) {
  const config = {
    placed: 'bg-info/20 text-info',
    accepted: 'bg-brand-200 text-brand-700',
    preparing: 'bg-warning/20 text-warning',
    picked_up: 'bg-warning/20 text-warning',
    out_for_delivery: 'bg-warning/20 text-warning',
    delivered: 'bg-success/20 text-success',
    cancelled: 'bg-danger/20 text-danger',
  }
  return (
    <span className={`px-2 py-1 rounded-lg text-xs font-bold ${config[status] || 'bg-muted/20 text-muted'}`}>
      {status?.replace('_', ' ').toUpperCase()}
    </span>
  )
}
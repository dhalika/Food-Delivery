import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import { OrderStatusSocket } from '../../websocket/orderStatusSocket'
import { useAuthStore } from '../../store/authStore'
import { Loader2, ArrowLeft, MapPin, Phone, Package, Clock, CheckCircle, XCircle, Truck } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const STAGES = [
  { key: 'placed', label: 'Placed', icon: <Package /> },
  { key: 'accepted', label: 'Accepted', icon: <CheckCircle /> },
  { key: 'preparing', label: 'Preparing', icon: <Clock /> },
  { key: 'picked_up', label: 'Picked Up', icon: <Package /> },
  { key: 'out_for_delivery', label: 'On the Way', icon: <Truck /> },
  { key: 'delivered', label: 'Delivered', icon: <CheckCircle /> },
]

export default function OrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { accessToken } = useAuthStore()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentStatus, setCurrentStatus] = useState('')

  useEffect(() => {
    load()
    // Connect WebSocket for live status updates
    const socket = new OrderStatusSocket(id, accessToken, (data) => {
      if (data.type === 'status_update' || data.type === 'current_status') {
        setCurrentStatus(data.status)
        if (data.type === 'status_update') {
          toast.success(`Order ${data.status.replace('_', ' ')}! 🎉`)
          load()
        }
      }
    })
    socket.connect()
    return () => socket.disconnect()
  }, [id])

  const load = async () => {
    try {
      const res = await customerAPI.orderDetail(id)
      setOrder(res)
      setCurrentStatus(res.status)
    } finally { setLoading(false) }
  }

  const handleCancel = async () => {
    const reason = prompt('Reason for cancellation?')
    if (!reason) return
    try {
      await customerAPI.cancelOrder(id, reason)
      toast.success('Order cancelled')
      load()
    } catch {}
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>
  if (!order) return <div className="card text-center py-12">Order not found</div>

  const currentStageIdx = STAGES.findIndex(s => s.key === currentStatus)
  const isActive = !['delivered', 'cancelled'].includes(currentStatus)

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button onClick={() => navigate('/customer/orders')} className="flex items-center gap-1 text-muted hover:text-dark">
        <ArrowLeft size={18} /> Back to orders
      </button>

      <div>
        <h1 className="text-3xl font-display font-bold">Order #{id.slice(0, 8).toUpperCase()}</h1>
        <p className="text-muted mt-1">Placed on {format(new Date(order.placed_at), 'MMM d, yyyy • h:mm a')}</p>
      </div>

      {/* STATUS TIMELINE */}
      {currentStatus === 'cancelled' ? (
        <div className="card bg-danger/10 border-2 border-danger/30 text-center py-8">
          <XCircle size={60} className="mx-auto text-danger mb-3" />
          <h3 className="text-xl font-bold text-danger">Order Cancelled</h3>
          {order.cancel_reason && <p className="text-sm text-muted mt-2">Reason: {order.cancel_reason}</p>}
        </div>
      ) : (
        <div className="card">
          <h3 className="font-bold text-lg mb-6">📍 Order Status</h3>
          <div className="relative">
            {STAGES.map((stage, idx) => {
              const isDone = idx <= currentStageIdx
              const isCurrent = idx === currentStageIdx && isActive
              return (
                <div key={stage.key} className="flex items-center gap-4 pb-6 relative">
                  {idx < STAGES.length - 1 && (
                    <div className={`absolute left-5 top-10 w-0.5 h-full ${isDone ? 'bg-success' : 'bg-gray-200'}`}></div>
                  )}
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center z-10 ${isDone ? 'bg-success text-white' : 'bg-gray-200 text-gray-400'} ${isCurrent ? 'animate-pulse ring-4 ring-success/30' : ''}`}>
                    {stage.icon}
                  </div>
                  <div>
                    <p className={`font-semibold ${isDone ? 'text-dark' : 'text-muted'}`}>{stage.label}</p>
                    {isCurrent && <p className="text-xs text-success font-bold">● LIVE</p>}
                  </div>
                </div>
              )
            })}
          </div>

          {isActive && ['picked_up', 'out_for_delivery'].includes(currentStatus) && (
            <button onClick={() => navigate(`/customer/orders/${id}/track`)} className="btn-primary w-full mt-4">
              🗺️ Track on Map
            </button>
          )}
        </div>
      )}

      {/* RESTAURANT */}
      <div className="card">
        <h3 className="font-bold text-lg mb-3">🏪 Restaurant</h3>
        <div className="flex items-center gap-3">
          {order.restaurant?.logo_url ? (
            <img src={order.restaurant.logo_url} alt="" className="w-14 h-14 rounded-xl" />
          ) : (
            <div className="w-14 h-14 rounded-xl bg-brand-400 flex items-center justify-center text-2xl">🍽️</div>
          )}
          <div>
            <p className="font-bold">{order.restaurant?.name}</p>
            <a href={`tel:${order.restaurant?.phone}`} className="text-sm text-muted flex items-center gap-1 hover:text-brand-600">
              <Phone size={12} /> {order.restaurant?.phone}
            </a>
          </div>
        </div>
      </div>

      {/* DELIVERY PARTNER */}
      {order.delivery_partner && (
        <div className="card">
          <h3 className="font-bold text-lg mb-3">🛵 Delivery Partner</h3>
          <div className="flex justify-between items-center">
            <div>
              <p className="font-bold">{order.delivery_partner.name}</p>
              <a href={`tel:${order.delivery_partner.phone}`} className="text-sm text-muted flex items-center gap-1">
                <Phone size={12} /> {order.delivery_partner.phone}
              </a>
            </div>
            <a href={`tel:${order.delivery_partner.phone}`} className="btn-secondary px-4 py-2 text-sm">Call</a>
          </div>
        </div>
      )}

      {/* ITEMS */}
      <div className="card">
        <h3 className="font-bold text-lg mb-3">🍽️ Items</h3>
        <div className="space-y-2 divide-y">
          {order.items?.map((item, i) => (
            <div key={i} className="flex justify-between pt-2 first:pt-0">
              <div>
                <p className="font-semibold">{item.name} × {item.quantity}</p>
                <p className="text-xs text-muted">₹{item.price} each</p>
              </div>
              <p className="font-bold">₹{item.subtotal}</p>
            </div>
          ))}
        </div>
      </div>

      {/* BILL */}
      <div className="card bg-cream">
        <h3 className="font-bold text-lg mb-3">💰 Bill</h3>
        <div className="space-y-1 text-sm">
          <Row label="Subtotal" value={`₹${order.item_total}`} />
          {order.discount_amount > 0 && <Row label="Discount" value={`-₹${order.discount_amount}`} color="text-success" />}
          <Row label="Delivery Fee" value={`₹${order.delivery_fee}`} />
          <Row label="Taxes" value={`₹${order.tax_amount}`} />
          <div className="border-t pt-2 flex justify-between font-bold text-lg">
            <span>Total Paid</span>
            <span>₹{order.final_amount}</span>
          </div>
          <p className="text-xs text-muted">via {order.payment_method?.toUpperCase()}</p>
        </div>
      </div>

      {/* ADDRESS */}
      <div className="card">
        <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
          <MapPin className="text-brand-600" size={18} /> Delivery Address
        </h3>
        <p className="text-sm text-muted">{order.delivery_address?.full_address}, {order.delivery_address?.city}</p>
      </div>

      {/* ACTIONS */}
      {currentStatus === 'placed' && (
        <button onClick={handleCancel} className="btn-secondary w-full border-danger text-danger">Cancel Order</button>
      )}
      {currentStatus === 'delivered' && (
        <button onClick={() => navigate(`/customer/orders/${id}/review`)} className="btn-primary w-full">
          ⭐ Rate your experience
        </button>
      )}
    </div>
  )
}

function Row({ label, value, color = 'text-dark' }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted">{label}</span>
      <span className={`font-semibold ${color}`}>{value}</span>
    </div>
  )
}
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { deliveryAPI } from '../../api/delivery'
import { Loader2, Package, Phone, MapPin, CheckCircle, Truck, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'

export default function AssignedOrders() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    load()
    const timer = setInterval(load, 10000)
    return () => clearInterval(timer)
  }, [])

  const load = async () => {
    try {
      const res = await deliveryAPI.myOrders()
      setOrders(res.orders || [])
    } finally { setLoading(false) }
  }

  const handlePickup = async (id) => {
    try { await deliveryAPI.pickup(id); toast.success('Picked up! 📦'); load() } catch {}
  }

  const handleOutForDelivery = async (id) => {
    try { await deliveryAPI.outForDelivery(id); toast.success('On the way! 🛵'); load() } catch {}
  }

  const handleDeliver = async (id) => {
    if (!confirm('Confirm delivery completion?')) return
    try { await deliveryAPI.deliver(id); toast.success('Delivered! 🎉'); load() } catch {}
  }

  const handleShareLocation = async (orderId) => {
    if (!navigator.geolocation) return toast.error('GPS not supported')
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          await deliveryAPI.updateLocation(orderId, pos.coords.latitude, pos.coords.longitude)
          toast.success('📍 Location shared!')
        } catch {}
      },
      () => toast.error('Could not get location')
    )
  }

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">Active Orders</h1>

      {orders.length === 0 ? (
        <div className="card text-center py-12">
          <Package size={48} className="mx-auto text-muted mb-3" />
          <h3 className="text-xl font-bold mb-1">No active orders</h3>
          <p className="text-muted">Toggle online to receive new assignments!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((o) => (
            <div key={o.id} className="card">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <p className="font-bold">Order #{o.id.slice(0, 8).toUpperCase()}</p>
                  <StatusBadge status={o.status} />
                </div>
                <p className="text-xl font-bold">₹{o.final_amount}</p>
              </div>

              {/* Restaurant */}
              <div className="bg-cream rounded-xl p-3 mb-2">
                <p className="text-xs text-muted">PICKUP FROM</p>
                <p className="font-bold">🏪 {o.restaurant?.name}</p>
                <p className="text-sm text-muted">{o.restaurant?.address}</p>
                <a href={`tel:${o.restaurant?.phone}`} className="text-xs text-brand-600 flex items-center gap-1 mt-1">
                  <Phone size={12} /> {o.restaurant?.phone}
                </a>
              </div>

              <div className="text-center my-1">
                <ArrowRight size={20} className="mx-auto text-muted rotate-90" />
              </div>

              {/* Customer */}
              <div className="bg-cream rounded-xl p-3 mb-3">
                <p className="text-xs text-muted">DELIVER TO</p>
                <p className="font-bold">🏠 {o.customer?.name}</p>
                <p className="text-sm text-muted">{o.delivery_address?.full_address}, {o.delivery_address?.city}</p>
                <a href={`tel:${o.customer?.phone}`} className="text-xs text-brand-600 flex items-center gap-1 mt-1">
                  <Phone size={12} /> {o.customer?.phone}
                </a>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button onClick={() => handleShareLocation(o.id)} className="btn-secondary text-sm flex items-center gap-1">
                  <MapPin size={14} /> Share GPS
                </button>

                {o.status === 'preparing' && (
                  <button onClick={() => handlePickup(o.id)} className="btn-primary text-sm flex-1 flex items-center justify-center gap-1">
                    <Package size={14} /> Pickup
                  </button>
                )}
                {o.status === 'picked_up' && (
                  <button onClick={() => handleOutForDelivery(o.id)} className="btn-primary text-sm flex-1 flex items-center justify-center gap-1">
                    <Truck size={14} /> Out for Delivery
                  </button>
                )}
                {o.status === 'out_for_delivery' && (
                  <button onClick={() => handleDeliver(o.id)} className="btn-primary text-sm flex-1 flex items-center justify-center gap-1 bg-success text-white hover:bg-success/80">
                    <CheckCircle size={14} /> Mark Delivered
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

function StatusBadge({ status }) {
  const config = {
    accepted: 'bg-brand-200 text-brand-700',
    preparing: 'bg-warning/20 text-warning',
    picked_up: 'bg-info/20 text-info',
    out_for_delivery: 'bg-info/20 text-info',
  }
  return <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${config[status] || 'bg-muted/20'} mt-1`}>{status?.replace('_', ' ').toUpperCase()}</span>
}
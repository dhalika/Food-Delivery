import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import { customerAPI } from '../../api/customer'
import { DeliveryTrackingSocket } from '../../websocket/deliveryTrackingSocket'
import { OrderStatusSocket } from '../../websocket/orderStatusSocket'
import { useAuthStore } from '../../store/authStore'
import { Loader2, ArrowLeft, Phone, Truck } from 'lucide-react'
import toast from 'react-hot-toast'

// Custom icons
const restaurantIcon = L.divIcon({
  html: '<div style="font-size:30px;">🏪</div>',
  iconSize: [40, 40],
  className: 'bg-transparent border-0',
})
const customerIcon = L.divIcon({
  html: '<div style="font-size:30px;">🏠</div>',
  iconSize: [40, 40],
  className: 'bg-transparent border-0',
})
const partnerIcon = L.divIcon({
  html: '<div style="font-size:30px;animation:pulse 1.5s infinite;">🛵</div>',
  iconSize: [40, 40],
  className: 'bg-transparent border-0',
})

export default function OrderTracking() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { accessToken } = useAuthStore()
  const [tracking, setTracking] = useState(null)
  const [loading, setLoading] = useState(true)
  const [partnerLocation, setPartnerLocation] = useState(null)
  const [status, setStatus] = useState('')

  useEffect(() => {
    load()

    // WebSocket for live location
    const locSocket = new DeliveryTrackingSocket(id, accessToken, (loc) => {
      setPartnerLocation({ lat: loc.lat, lng: loc.lng })
    })
    locSocket.connect()

    // WebSocket for status
    const statusSocket = new OrderStatusSocket(id, accessToken, (data) => {
      if (data.status) {
        setStatus(data.status)
        if (data.type === 'status_update') {
          toast.success(`Status: ${data.status.replace('_', ' ')}`)
        }
      }
    })
    statusSocket.connect()

    return () => {
      locSocket.disconnect()
      statusSocket.disconnect()
    }
  }, [id])

  const load = async () => {
    try {
      const res = await customerAPI.trackOrder(id)
      setTracking(res)
      setStatus(res.status)
      if (res.current_location) {
        setPartnerLocation({ lat: res.current_location.lat, lng: res.current_location.lng })
      }
    } finally { setLoading(false) }
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>
  if (!tracking) return <div className="card text-center py-12">Tracking data not available</div>

  const restLat = tracking.restaurant?.lat
  const restLng = tracking.restaurant?.lng
  const delLat = tracking.delivery_address?.lat
  const delLng = tracking.delivery_address?.lng

  const center = partnerLocation || { lat: restLat || 17.4, lng: restLng || 78.4 }
  const points = [
    [restLat, restLng],
    ...(partnerLocation ? [[partnerLocation.lat, partnerLocation.lng]] : []),
    [delLat, delLng],
  ].filter(p => p[0] && p[1])

  return (
    <div className="space-y-4">
      <button onClick={() => navigate(`/customer/orders/${id}`)} className="flex items-center gap-1 text-muted hover:text-dark">
        <ArrowLeft size={18} /> Order details
      </button>

      <div className="card bg-gradient-to-r from-brand-400 to-brand-500">
        <div className="flex items-center gap-3">
          <div className="text-4xl animate-bounce">🛵</div>
          <div>
            <h2 className="text-xl font-display font-extrabold">Live Tracking</h2>
            <p className="text-sm font-semibold">
              {status === 'picked_up' && 'Picked up from restaurant'}
              {status === 'out_for_delivery' && 'On the way to you!'}
              {status === 'delivered' && 'Delivered! 🎉'}
              {!['picked_up', 'out_for_delivery', 'delivered'].includes(status) && 'Preparing your order...'}
            </p>
          </div>
        </div>
      </div>

      {/* MAP */}
      <div className="card p-0 overflow-hidden" style={{ height: '500px' }}>
        {restLat && delLat ? (
          <MapContainer center={[center.lat, center.lng]} zoom={14} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='© OpenStreetMap'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {/* Restaurant */}
            <Marker position={[restLat, restLng]} icon={restaurantIcon}>
              <Popup>🏪 {tracking.restaurant?.name}</Popup>
            </Marker>
            {/* Customer */}
            <Marker position={[delLat, delLng]} icon={customerIcon}>
              <Popup>🏠 Delivery Address</Popup>
            </Marker>
            {/* Delivery partner */}
            {partnerLocation && (
              <Marker position={[partnerLocation.lat, partnerLocation.lng]} icon={partnerIcon}>
                <Popup>🛵 {tracking.delivery_partner?.name || 'Delivery Partner'}</Popup>
              </Marker>
            )}
            {/* Route line */}
            <Polyline positions={points} color="#FFC72C" weight={4} dashArray="10,10" />
          </MapContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-muted">
            <p>Location data not available</p>
          </div>
        )}
      </div>

      {/* DELIVERY PARTNER CARD */}
      {tracking.delivery_partner && (
        <div className="card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-brand-400 rounded-full flex items-center justify-center text-2xl">🛵</div>
            <div>
              <p className="font-bold">{tracking.delivery_partner.name}</p>
              <p className="text-xs text-muted">Your delivery partner</p>
            </div>
          </div>
          <a href={`tel:${tracking.delivery_partner.phone}`} className="btn-primary px-4 py-2 flex items-center gap-1">
            <Phone size={16} /> Call
          </a>
        </div>
      )}

      {/* STATUS BADGE */}
      {!partnerLocation && (
        <div className="card text-center py-6">
          <Truck size={40} className="mx-auto text-muted mb-2" />
          <p className="text-muted">Partner will appear on map once they start delivery</p>
        </div>
      )}
    </div>
  )
}
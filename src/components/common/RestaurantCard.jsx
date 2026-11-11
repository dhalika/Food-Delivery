import { Star, Clock, Tag } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function RestaurantCard({ restaurant }) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/customer/restaurants/${restaurant.id}`)}
      className="card cursor-pointer hover:shadow-brand hover:-translate-y-1 transition-all duration-300 p-0 overflow-hidden"
    >
      {/* Banner */}
      <div className="relative h-40 bg-gradient-to-br from-brand-200 to-brand-400">
        {restaurant.banner_url ? (
          <img src={restaurant.banner_url} alt={restaurant.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-6xl">🍽️</div>
        )}
        {!restaurant.is_active && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
            <span className="bg-white px-3 py-1 rounded-full text-xs font-bold">CLOSED</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-display font-bold text-lg text-dark line-clamp-1">
            {restaurant.name}
          </h3>
          <div className="flex items-center gap-1 bg-success/10 text-success px-2 py-0.5 rounded-md">
            <Star size={14} fill="currentColor" />
            <span className="text-sm font-bold">{restaurant.avg_rating || '0.0'}</span>
          </div>
        </div>

        <p className="text-muted text-sm mt-1 line-clamp-1">{restaurant.cuisine_type}</p>

        <div className="flex items-center gap-4 mt-3 text-xs text-muted">
          {restaurant.avg_delivery_time && (
            <span className="flex items-center gap-1">
              <Clock size={14} /> {restaurant.avg_delivery_time} min
            </span>
          )}
          <span className="flex items-center gap-1">
            <Tag size={14} /> ₹{restaurant.min_order_value} min
          </span>
          {restaurant.distance_km && (
            <span>📍 {restaurant.distance_km} km</span>
          )}
        </div>
      </div>
    </div>
  )
}
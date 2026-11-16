import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import { useCart } from '../../hooks/useCart'
import { Star, Clock, Tag, MapPin, Phone, Loader2, Plus, ArrowLeft, Users } from 'lucide-react'

export default function RestaurantDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { addItem, refreshCart } = useCart()
  const [restaurant, setRestaurant] = useState(null)
  const [menu, setMenu] = useState([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(null)

  useEffect(() => { load(); refreshCart() }, [id])

  const load = async () => {
    try {
      const [r, m] = await Promise.all([
        customerAPI.getRestaurant(id),
        customerAPI.getMenu(id),
      ])
      setRestaurant(r)
      setMenu(m.menu || [])
    } finally { setLoading(false) }
  }

  const handleAdd = async (item) => {
    setAdding(item.id)
    await addItem(item.id, 1)
    setAdding(null)
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>
  if (!restaurant) return <div className="card text-center py-12">Restaurant not found</div>

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-muted hover:text-dark">
        <ArrowLeft size={18} /> Back
      </button>

      <div className="card p-0 overflow-hidden">
        <div className="h-48 bg-gradient-to-br from-brand-300 to-brand-500">
          {restaurant.banner_url && <img src={restaurant.banner_url} alt="" className="w-full h-full object-cover" />}
        </div>
        <div className="p-6">
          <div className="flex justify-between items-start flex-wrap gap-3">
            <div>
              <h1 className="text-3xl font-display font-extrabold">{restaurant.name}</h1>
              <p className="text-muted mt-1">{restaurant.cuisine_type}</p>
            </div>
            <button
              onClick={() => navigate('/customer/group/create', { state: { restaurant_id: id } })}
              className="bg-gradient-to-r from-brand-500 to-brand-600 text-dark px-4 py-2 rounded-xl font-bold flex items-center gap-2 hover:shadow-brand transition-all"
            >
              <Users size={18} /> Create Group Order
            </button>
          </div>
          <div className="flex flex-wrap gap-3 mt-4">
            <Pill icon={<Star size={16} fill="currentColor" />} text={`${restaurant.avg_rating} (${restaurant.total_reviews})`} color="text-success" />
            {restaurant.avg_delivery_time && <Pill icon={<Clock size={16} />} text={`${restaurant.avg_delivery_time} min`} />}
            <Pill icon={<Tag size={16} />} text={`₹${restaurant.min_order_value} min`} />
          </div>
          <div className="mt-4 pt-4 border-t text-sm text-muted space-y-1">
            <p className="flex items-center gap-2"><MapPin size={14} /> {restaurant.address}, {restaurant.city}</p>
            <p className="flex items-center gap-2"><Phone size={14} /> {restaurant.phone}</p>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-display font-bold mb-4">🍽️ Menu</h2>
        {menu.length === 0 ? (
          <div className="card text-center py-8"><p className="text-muted">Menu coming soon!</p></div>
        ) : (
          <div className="space-y-6">
            {menu.map((cat) => (
              <div key={cat.category_id || 'uncat'}>
                <h3 className="text-xl font-display font-bold mb-3 text-brand-700">{cat.category_name}</h3>
                <div className="space-y-3">
                  {cat.items.map((item) => (
                    <div key={item.id} className="card flex gap-4 items-center">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`w-4 h-4 border-2 ${item.is_veg ? 'border-success' : 'border-danger'} flex items-center justify-center rounded-sm`}>
                            <span className={`w-2 h-2 rounded-full ${item.is_veg ? 'bg-success' : 'bg-danger'}`}></span>
                          </span>
                          <h4 className="font-bold">{item.name}</h4>
                        </div>
                        <p className="text-sm text-muted mb-2 line-clamp-2">{item.description}</p>
                        <p className="font-bold text-lg">₹{item.price}</p>
                      </div>
                      <div className="flex flex-col items-center gap-2">
                        {item.image_url ? (
                          <img src={item.image_url} alt="" className="w-24 h-24 rounded-xl object-cover" />
                        ) : (
                          <div className="w-24 h-24 rounded-xl bg-gradient-to-br from-brand-200 to-brand-400 flex items-center justify-center text-4xl">🍽️</div>
                        )}
                        <button
                          onClick={() => handleAdd(item)}
                          disabled={!item.is_available || adding === item.id}
                          className="btn-primary py-2 px-4 text-sm flex items-center gap-1 disabled:opacity-50"
                        >
                          {adding === item.id ? <Loader2 size={14} className="animate-spin" /> : <Plus size={16} />}
                          Add
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Pill({ icon, text, color = 'text-dark' }) {
  return (
    <div className={`flex items-center gap-1 bg-cream px-3 py-1 rounded-lg ${color} font-semibold text-sm`}>
      {icon} {text}
    </div>
  )
}
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import RestaurantCard from '../../components/common/RestaurantCard'
import SearchBar from '../../components/common/SearchBar'
import { Loader2 } from 'lucide-react'

const CUISINES = [
  { name: 'Pizza', emoji: '🍕' },
  { name: 'Biryani', emoji: '🍚' },
  { name: 'Chinese', emoji: '🥡' },
  { name: 'Burger', emoji: '🍔' },
  { name: 'South Indian', emoji: '🥘' },
  { name: 'North Indian', emoji: '🍛' },
  { name: 'Desserts', emoji: '🍰' },
  { name: 'Beverages', emoji: '🥤' },
]

export default function Home() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [restaurants, setRestaurants] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRestaurants()
  }, [])

  const loadRestaurants = async () => {
    try {
      const res = await customerAPI.listRestaurants({ limit: 8 })
      setRestaurants(res.restaurants || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* HERO */}
      <div className="bg-gradient-to-r from-brand-400 to-brand-500 rounded-3xl p-8 md:p-12 text-dark">
        <h1 className="text-3xl md:text-5xl font-display font-extrabold mb-3">
          Hungry? 🤤
        </h1>
        <p className="text-lg mb-6 opacity-90">
          Delicious food delivered in minutes
        </p>
        <SearchBar
          value={search}
          onChange={(v) => {
            setSearch(v)
            if (v.length > 2) navigate(`/customer/restaurants?search=${v}`)
          }}
        />
      </div>

      {/* CATEGORIES */}
      <section>
        <h2 className="text-2xl font-display font-bold mb-4">What's on your mind?</h2>
        <div className="grid grid-cols-4 md:grid-cols-8 gap-4">
          {CUISINES.map((c) => (
            <button
              key={c.name}
              onClick={() => navigate(`/customer/restaurants?cuisine_type=${c.name}`)}
              className="flex flex-col items-center gap-2 p-4 bg-white rounded-2xl hover:shadow-brand hover:-translate-y-1 transition-all"
            >
              <span className="text-4xl">{c.emoji}</span>
              <span className="text-xs font-semibold text-dark">{c.name}</span>
            </button>
          ))}
        </div>
      </section>

      {/* POPULAR RESTAURANTS */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-display font-bold">🔥 Popular Near You</h2>
          <button
            onClick={() => navigate('/customer/restaurants')}
            className="text-brand-600 font-semibold hover:underline"
          >
            View All →
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="animate-spin text-brand-500" size={32} />
          </div>
        ) : restaurants.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-muted">No restaurants yet. Check back soon!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {restaurants.map((r) => <RestaurantCard key={r.id} restaurant={r} />)}
          </div>
        )}
      </section>
    </div>
  )
}
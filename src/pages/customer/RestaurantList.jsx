import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import RestaurantCard from '../../components/common/RestaurantCard'
import SearchBar from '../../components/common/SearchBar'
import { Loader2, SlidersHorizontal } from 'lucide-react'

export default function RestaurantList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [restaurants, setRestaurants] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [cuisineFilter, setCuisineFilter] = useState(searchParams.get('cuisine_type') || '')

  useEffect(() => {
    loadData()
  }, [search, cuisineFilter])

  const loadData = async () => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      if (cuisineFilter) params.cuisine_type = cuisineFilter
      const res = await customerAPI.listRestaurants(params)
      setRestaurants(res.restaurants || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold mb-4">All Restaurants</h1>
        <SearchBar value={search} onChange={setSearch} />
      </div>

      {/* Filter chips */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <FilterChip label="All" active={!cuisineFilter} onClick={() => setCuisineFilter('')} />
        {['Pizza', 'Biryani', 'Chinese', 'Burger', 'Indian'].map((c) => (
          <FilterChip
            key={c}
            label={c}
            active={cuisineFilter === c}
            onClick={() => setCuisineFilter(c)}
          />
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="animate-spin text-brand-500" size={32} />
        </div>
      ) : restaurants.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-6xl mb-3">🔍</div>
          <h3 className="text-xl font-bold mb-1">No restaurants found</h3>
          <p className="text-muted">Try a different search</p>
        </div>
      ) : (
        <>
          <p className="text-muted text-sm">{restaurants.length} restaurants</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {restaurants.map((r) => <RestaurantCard key={r.id} restaurant={r} />)}
          </div>
        </>
      )}
    </div>
  )
}

function FilterChip({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2 rounded-full whitespace-nowrap font-semibold text-sm transition ${
        active
          ? 'bg-brand-500 text-dark shadow-brand'
          : 'bg-white text-muted hover:text-dark border border-gray-200'
      }`}
    >
      {label}
    </button>
  )
}
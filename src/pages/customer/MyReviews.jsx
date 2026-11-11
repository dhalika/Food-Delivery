import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import { Star, Loader2, Package } from 'lucide-react'
import { format } from 'date-fns'

export default function MyReviews() {
  const navigate = useNavigate()
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const res = await customerAPI.myReviews()
      setReviews(res.reviews || [])
    } finally { setLoading(false) }
  }

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">My Reviews</h1>

      {reviews.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-6xl mb-3">⭐</div>
          <h3 className="text-xl font-bold mb-1">No reviews yet</h3>
          <p className="text-muted mb-4">Order from restaurants and share your experience!</p>
          <button onClick={() => navigate('/customer/orders')} className="btn-primary">My Orders</button>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((r) => (
            <div key={r.id} className="card">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-bold">{r.restaurant_name}</h4>
                  <p className="text-xs text-muted">{format(new Date(r.created_at), 'MMM d, yyyy')}</p>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star key={s} size={18} fill={s <= r.rating ? '#FFC72C' : 'transparent'}
                      className={s <= r.rating ? 'text-brand-500' : 'text-gray-300'} />
                  ))}
                </div>
              </div>
              {r.comment && <p className="text-sm text-muted mt-2 italic">"{r.comment}"</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
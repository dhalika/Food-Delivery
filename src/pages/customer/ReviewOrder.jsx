import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import { Star, ArrowLeft, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ReviewOrder() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { load() }, [id])

  const load = async () => {
    try {
      const res = await customerAPI.orderDetail(id)
      setOrder(res)
    } finally { setLoading(false) }
  }

  const handleSubmit = async () => {
    if (rating === 0) return toast.error('Please select a rating')
    setSubmitting(true)
    try {
      await customerAPI.submitReview(id, rating, comment)
      toast.success('Thanks for your review! ⭐')
      navigate('/customer/orders')
    } catch {} finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-muted hover:text-dark">
        <ArrowLeft size={18} /> Back
      </button>

      <div className="card text-center">
        <div className="text-6xl mb-3">🙏</div>
        <h1 className="text-2xl font-display font-bold mb-2">How was your order?</h1>
        <p className="text-muted">from <b>{order?.restaurant?.name}</b></p>
      </div>

      <div className="card">
        <h3 className="font-bold mb-4">Rate your experience</h3>
        <div className="flex gap-2 justify-center">
          {[1, 2, 3, 4, 5].map((s) => (
            <button
              key={s}
              onClick={() => setRating(s)}
              onMouseEnter={() => setHover(s)}
              onMouseLeave={() => setHover(0)}
              className="transition-transform hover:scale-125"
            >
              <Star
                size={48}
                fill={s <= (hover || rating) ? '#FFC72C' : 'transparent'}
                className={s <= (hover || rating) ? 'text-brand-500' : 'text-gray-300'}
                strokeWidth={1.5}
              />
            </button>
          ))}
        </div>
        {rating > 0 && (
          <p className="text-center mt-3 text-sm font-semibold text-brand-700">
            {['', 'Poor 😞', 'Average 😐', 'Good 🙂', 'Great 😊', 'Excellent! 🤩'][rating]}
          </p>
        )}
      </div>

      <div className="card">
        <h3 className="font-bold mb-3">Share your experience (optional)</h3>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Tell us what you liked or what could be better..."
          rows={5}
          maxLength={500}
          className="input-field resize-none"
        />
        <p className="text-xs text-muted mt-1 text-right">{comment.length}/500</p>
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting || rating === 0}
        className="btn-primary w-full text-lg py-4 flex items-center justify-center gap-2"
      >
        {submitting ? <Loader2 className="animate-spin" /> : <Star size={20} />}
        {submitting ? 'Submitting...' : 'Submit Review'}
      </button>
    </div>
  )
}
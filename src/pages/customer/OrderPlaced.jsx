import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { CheckCircle, Package, Home } from 'lucide-react'

export default function OrderPlaced() {
  const navigate = useNavigate()
  const location = useLocation()
  const { id } = useParams()
  const { order } = location.state || {}

  return (
    <div className="max-w-md mx-auto py-8">
      <div className="card text-center">
        <div className="w-24 h-24 mx-auto bg-success/20 rounded-full flex items-center justify-center mb-4 animate-slide-up">
          <CheckCircle size={60} className="text-success" />
        </div>

        <h1 className="text-3xl font-display font-extrabold mb-2">Order Placed! 🎉</h1>
        <p className="text-muted mb-6">Your order is confirmed and being prepared</p>

        {order && (
          <div className="bg-cream rounded-xl p-4 mb-6 text-left">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted">Order ID:</span>
              <span className="font-bold">#{id?.slice(0, 8).toUpperCase()}</span>
            </div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted">Total:</span>
              <span className="font-bold">₹{order.final_amount}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted">Payment:</span>
              <span className="font-bold uppercase">{order.payment_method}</span>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <button onClick={() => navigate(`/customer/orders/${id}/track`)} className="btn-primary w-full flex items-center justify-center gap-2">
            <Package size={20} /> Track Order
          </button>
          <button onClick={() => navigate('/customer')} className="btn-secondary w-full flex items-center justify-center gap-2">
            <Home size={20} /> Back to Home
          </button>
        </div>
      </div>
    </div>
  )
}
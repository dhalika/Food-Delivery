import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cartAPI } from '../../api/cart'
import { useCart } from '../../hooks/useCart'
import { Loader2, Minus, Plus, Trash2, Tag, ShoppingBag, X } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Cart() {
  const navigate = useNavigate()
  const { updateQty, removeItem, clearAll, refreshCart } = useCart()
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [couponCode, setCouponCode] = useState('')
  const [appliedCoupon, setAppliedCoupon] = useState(null)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const c = await cartAPI.getCart()
      setCart(c)
      await refreshCart()
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const handleQty = async (itemId, newQty) => {
    await updateQty(itemId, newQty)
    load()
  }

  const handleRemove = async (itemId) => {
    await removeItem(itemId)
    load()
  }

  const handleApplyCoupon = async () => {
    if (!couponCode.trim()) return
    try {
      const res = await cartAPI.applyCoupon(couponCode.toUpperCase())
      setAppliedCoupon(res)
      toast.success(`₹${res.discount} off! 🎉`)
    } catch {}
  }

  const removeCoupon = () => {
    setAppliedCoupon(null)
    setCouponCode('')
  }

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="card text-center py-16 max-w-md mx-auto">
        <div className="text-7xl mb-4">🛒</div>
        <h2 className="text-2xl font-display font-bold mb-2">Cart is Empty</h2>
        <p className="text-muted mb-6">Browse restaurants and add items!</p>
        <button onClick={() => navigate('/customer')} className="btn-primary">
          Explore Restaurants
        </button>
      </div>
    )
  }

  const subtotal = cart.subtotal || 0
  const discount = appliedCoupon?.discount || 0
  const deliveryFee = 30
  const tax = Math.round((subtotal - discount) * 0.05)
  const total = subtotal - discount + deliveryFee + tax

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* LEFT - Items */}
      <div className="lg:col-span-2 space-y-4">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-display font-bold">Your Cart</h1>
          <button onClick={() => { clearAll(); load() }} className="text-sm text-danger hover:underline flex items-center gap-1">
            <Trash2 size={14} /> Clear all
          </button>
        </div>

        {/* Restaurant info */}
        {cart.restaurant && (
          <div className="card bg-cream flex items-center gap-3">
            <ShoppingBag className="text-brand-600" />
            <div>
              <p className="text-xs text-muted">Ordering from</p>
              <p className="font-bold">{cart.restaurant.name}</p>
            </div>
          </div>
        )}

        {cart.items.map((item) => (
          <div key={item.id} className="card flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-brand-200 to-brand-400 rounded-xl flex items-center justify-center text-3xl">
              🍽️
            </div>
            <div className="flex-1">
              <h4 className="font-bold">{item.name}</h4>
              <p className="text-sm text-muted">₹{item.price} each</p>
            </div>
            <div className="flex items-center gap-2 bg-cream rounded-lg">
              <button onClick={() => handleQty(item.id, item.quantity - 1)} className="p-2 hover:bg-brand-200 rounded-l-lg"><Minus size={16} /></button>
              <span className="font-bold w-6 text-center">{item.quantity}</span>
              <button onClick={() => handleQty(item.id, item.quantity + 1)} className="p-2 hover:bg-brand-200 rounded-r-lg"><Plus size={16} /></button>
            </div>
            <div className="text-right">
              <p className="font-bold">₹{item.subtotal}</p>
              <button onClick={() => handleRemove(item.id)} className="text-danger text-xs hover:underline">Remove</button>
            </div>
          </div>
        ))}
      </div>

      {/* RIGHT - Summary */}
      <div className="lg:col-span-1">
        <div className="card sticky top-24 space-y-4">
          <h3 className="font-display font-bold text-xl">Bill Details</h3>

          {/* Coupon */}
          {!appliedCoupon ? (
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Tag className="absolute left-3 top-1/2 -translate-y-1/2 text-brand-600" size={18} />
                <input
                  type="text"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  placeholder="Coupon code"
                  className="input-field pl-10 uppercase"
                />
              </div>
              <button onClick={handleApplyCoupon} className="btn-primary px-4">Apply</button>
            </div>
          ) : (
            <div className="bg-success/10 border border-success/30 p-3 rounded-xl flex justify-between items-center">
              <div>
                <p className="font-bold text-success text-sm">✓ {appliedCoupon.code} applied</p>
                <p className="text-xs text-muted">You saved ₹{appliedCoupon.discount}</p>
              </div>
              <button onClick={removeCoupon} className="text-muted hover:text-dark"><X size={18} /></button>
            </div>
          )}

          <div className="border-t pt-4 space-y-2 text-sm">
            <Row label="Subtotal" value={`₹${subtotal}`} />
            {discount > 0 && <Row label="Discount" value={`-₹${discount}`} color="text-success" />}
            <Row label="Delivery Fee" value={`₹${deliveryFee}`} />
            <Row label="Taxes (5%)" value={`₹${tax}`} />
            <div className="border-t pt-2 flex justify-between font-bold text-lg">
              <span>Total</span>
              <span>₹{total}</span>
            </div>
          </div>

          <button
            onClick={() => navigate('/customer/checkout', { state: { cart, appliedCoupon, total } })}
            className="btn-primary w-full"
          >
            Proceed to Checkout →
          </button>
        </div>
      </div>
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
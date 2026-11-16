import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import { paymentAPI } from '../../api/payment'
import { useCart } from '../../hooks/useCart'
import { useAuthStore } from '../../store/authStore'
import { loadRazorpayScript, openRazorpayCheckout } from '../../utils/razorpay'
import { MapPin, CreditCard, Wallet, ArrowLeft, Loader2, Plus, Home, Briefcase } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Checkout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuthStore()
  const { clearAll } = useCart()
  const { cart, appliedCoupon, total } = location.state || {}

  const [addresses, setAddresses] = useState([])
  const [selectedAddress, setSelectedAddress] = useState(null)
  const [paymentMethod, setPaymentMethod] = useState('razorpay')
  const [instructions, setInstructions] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingAddr, setLoadingAddr] = useState(true)

  useEffect(() => {
    if (!cart) { navigate('/customer/cart'); return }
    loadAddresses()
  }, [])

  const loadAddresses = async () => {
    try {
      const res = await customerAPI.listAddresses()
      setAddresses(res.addresses || [])
      const def = res.addresses.find(a => a.is_default) || res.addresses[0]
      setSelectedAddress(def)
    } finally { setLoadingAddr(false) }
  }

  const handlePlaceOrder = async () => {
    if (!selectedAddress) return toast.error('Please select delivery address')
    setLoading(true)

    try {
      // 1. Place order
      const orderRes = await customerAPI.placeOrder({
        delivery_address_id: selectedAddress.id,
        payment_method: paymentMethod,
        coupon_code: appliedCoupon?.code || '',
        special_instructions: instructions,
      })

      // 2. If COD, done
      if (paymentMethod === 'cod') {
        toast.success('Order placed! 🎉')
        clearAll()
        navigate(`/customer/orders/${orderRes.order_id}/success`, { state: { order: orderRes } })
        return
      }

      // 3. Razorpay flow
      const loaded = await loadRazorpayScript()
      if (!loaded) throw new Error('Razorpay failed to load')

      const payRes = await paymentAPI.createOrder(orderRes.order_id)

      openRazorpayCheckout({
        razorpay_key_id: payRes.razorpay_key_id,
        razorpay_order_id: payRes.razorpay_order_id,
        amount: payRes.amount,
        description: `HongKong Order #${orderRes.order_id.slice(0, 8)}`,
        prefill: { name: user?.name, email: user?.email, contact: user?.phone },
        onSuccess: async (response) => {
          try {
            await paymentAPI.verifyPayment(response)
            toast.success('Payment successful! 🎉')
            clearAll()
            navigate(`/customer/orders/${orderRes.order_id}/success`, { state: { order: orderRes } })
          } catch {
            toast.error('Payment verification failed')
          }
        },
        onFailure: async () => {
          toast.error('Payment cancelled')
          await paymentAPI.markFailed(orderRes.order_id)
        },
      })

    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (!cart) return null

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button onClick={() => navigate('/customer/cart')} className="flex items-center gap-1 text-muted hover:text-dark">
        <ArrowLeft size={18} /> Back to cart
      </button>

      <h1 className="text-3xl font-display font-bold">Checkout</h1>

      {/* DELIVERY ADDRESS */}
      <div className="card">
        <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
          <MapPin className="text-brand-600" /> Delivery Address
        </h3>

        {loadingAddr ? (
          <Loader2 className="animate-spin" />
        ) : addresses.length === 0 ? (
          <div className="text-center py-6">
            <p className="text-muted mb-3">No saved addresses</p>
            <button onClick={() => navigate('/customer/addresses')} className="btn-primary">
              <Plus size={18} className="inline mr-1" /> Add Address
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {addresses.map((addr) => (
              <label key={addr.id} className={`block p-3 rounded-xl cursor-pointer border-2 ${selectedAddress?.id === addr.id ? 'border-brand-500 bg-brand-50' : 'border-gray-200'}`}>
                <div className="flex items-start gap-3">
                  <input type="radio" name="addr" checked={selectedAddress?.id === addr.id} onChange={() => setSelectedAddress(addr)} className="mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      {addr.label === 'home' ? <Home size={16} /> : <Briefcase size={16} />}
                      <span className="font-bold capitalize">{addr.label}</span>
                      {addr.is_default && <span className="text-xs bg-brand-500 px-2 py-0.5 rounded-full">Default</span>}
                    </div>
                    <p className="text-sm text-muted mt-1">{addr.full_address}, {addr.city} - {addr.pincode}</p>
                  </div>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* PAYMENT METHOD */}
      <div className="card">
        <h3 className="font-bold text-lg mb-3">💳 Payment Method</h3>
        <div className="space-y-2">
          <PaymentOption
            selected={paymentMethod === 'razorpay'}
            onClick={() => setPaymentMethod('razorpay')}
            icon={<CreditCard />}
            title="Razorpay"
            desc="UPI, Cards, Netbanking, Wallets"
          />
          <PaymentOption
            selected={paymentMethod === 'cod'}
            onClick={() => setPaymentMethod('cod')}
            icon={<Wallet />}
            title="Cash on Delivery"
            desc="Pay when order arrives"
          />
        </div>
      </div>

      {/* INSTRUCTIONS */}
      <div className="card">
        <h3 className="font-bold text-lg mb-3">📝 Instructions (Optional)</h3>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="E.g. Extra spicy, no onions, call on arrival..."
          rows={2}
          className="input-field resize-none"
        />
      </div>

      {/* ORDER SUMMARY */}
      <div className="card bg-cream">
        <h3 className="font-bold text-lg mb-3">🧾 Order Summary</h3>
        <div className="text-sm space-y-1">
          <Row label="Subtotal" value={`₹${cart.subtotal}`} />
          {appliedCoupon && <Row label={`Discount (${appliedCoupon.code})`} value={`-₹${appliedCoupon.discount}`} color="text-success" />}
          <Row label="Delivery Fee" value="₹30" />
          <Row label="Taxes (5%)" value={`₹${Math.round((cart.subtotal - (appliedCoupon?.discount || 0)) * 0.05)}`} />
          <div className="border-t pt-2 mt-2 flex justify-between font-bold text-xl">
            <span>Total</span>
            <span className="text-brand-700">₹{total}</span>
          </div>
        </div>
      </div>

      <button
        onClick={handlePlaceOrder}
        disabled={loading || !selectedAddress}
        className="btn-primary w-full text-lg py-4 flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="animate-spin" /> : null}
        {loading ? 'Placing Order...' : `Place Order • ₹${total}`}
      </button>
    </div>
  )
}

function PaymentOption({ selected, onClick, icon, title, desc }) {
  return (
    <button onClick={onClick} className={`w-full p-4 rounded-xl border-2 text-left flex items-center gap-3 ${selected ? 'border-brand-500 bg-brand-50' : 'border-gray-200'}`}>
      <div className={`p-2 rounded-lg ${selected ? 'bg-brand-500' : 'bg-cream'}`}>{icon}</div>
      <div className="flex-1">
        <p className="font-bold">{title}</p>
        <p className="text-xs text-muted">{desc}</p>
      </div>
      <input type="radio" checked={selected} readOnly />
    </button>
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
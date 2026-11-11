import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { groupOrderAPI } from '../../api/groupOrder'
import { customerAPI } from '../../api/customer'
import { GroupOrderSocket } from '../../websocket/groupOrderSocket'
import { useAuthStore } from '../../store/authStore'
import { Loader2, Users, Copy, Share2, Trash2, X, ShoppingBag, Crown, UserPlus, ArrowLeft, Check } from 'lucide-react'
import toast from 'react-hot-toast'

export default function GroupOrderManage() {
  const { code } = useParams()
  const navigate = useNavigate()
  const { user, accessToken } = useAuthStore()
  const [groupInfo, setGroupInfo] = useState(null)
  const [liveState, setLiveState] = useState(null)
  const [menu, setMenu] = useState([])
  const [loading, setLoading] = useState(true)
  const [addresses, setAddresses] = useState([])
  const [selectedAddress, setSelectedAddress] = useState(null)
  const [paymentMethod, setPaymentMethod] = useState('cod')
  const [showCheckout, setShowCheckout] = useState(false)
  const [splits, setSplits] = useState(null)

  useEffect(() => {
    loadInitial()
  }, [code])

  const loadInitial = async () => {
    try {
      const info = await groupOrderAPI.getByCode(code)
      setGroupInfo(info)

      const menuRes = await customerAPI.getMenu(info.restaurant.id)
      setMenu(menuRes.menu || [])

      // Connect WebSocket
      const socket = new GroupOrderSocket(info.group_id, accessToken, (data) => {
        setLiveState(data)
      })
      socket.connect()

      // Load addresses if host
      if (info.is_host) {
        const addrs = await customerAPI.listAddresses()
        setAddresses(addrs.addresses || [])
        const def = addrs.addresses?.find(a => a.is_default) || addrs.addresses?.[0]
        setSelectedAddress(def)
      }

      return () => socket.disconnect()
    } catch (err) {
      navigate('/customer')
    } finally { setLoading(false) }
  }

  const handleAddItem = async (menuItem) => {
    try {
      await groupOrderAPI.addItem(groupInfo.group_id, menuItem.id, 1)
      toast.success(`Added ${menuItem.name}!`)
    } catch {}
  }

  const handleRemoveItem = async (itemId) => {
    try {
      await groupOrderAPI.removeItem(itemId)
      toast.success('Removed')
    } catch {}
  }

  const copyLink = () => {
    const link = `${window.location.origin}/customer/group/${code}`
    navigator.clipboard.writeText(link)
    toast.success('Link copied! 📋')
  }

  const shareWhatsApp = () => {
    const link = `${window.location.origin}/customer/group/${code}`
    const text = `🥡 Join my HongKong order from ${groupInfo.restaurant.name}!\nCode: ${code}\n${link}`
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank')
  }

  const handleFinalize = async () => {
    if (!selectedAddress) return toast.error('Select address')
    try {
      const res = await groupOrderAPI.finalize(groupInfo.group_id, {
        delivery_address_id: selectedAddress.id,
        payment_method: paymentMethod,
      })
      setSplits(res)
      toast.success('Group order placed! 🎉')
    } catch {}
  }

  const handleCancel = async () => {
    if (!confirm('Cancel group order?')) return
    try {
      await groupOrderAPI.cancel(groupInfo.group_id)
      toast.success('Cancelled')
      navigate('/customer')
    } catch {}
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-500" size={40} /></div>
  if (!groupInfo) return <div className="card text-center py-12">Group not found</div>

  const state = liveState || groupInfo
  const items = state.items || []
  const members = state.members || []
  const subtotal = state.subtotal || 0
  const myItems = items.filter(i => i.user_id === user.id)

  // SPLIT SUCCESS PAGE
  if (splits) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="card text-center bg-gradient-to-br from-success/20 to-success/5">
          <div className="text-6xl mb-3">🎉</div>
          <h1 className="text-3xl font-display font-bold mb-2">Group Order Placed!</h1>
          <p className="text-muted">Order #{splits.order_id.slice(0, 8).toUpperCase()}</p>
          <p className="text-4xl font-display font-extrabold mt-3">₹{splits.final_amount}</p>
        </div>

        <div className="card">
          <h3 className="font-bold text-lg mb-3">💰 Split Payment</h3>
          <p className="text-sm text-muted mb-3">Collect from each person:</p>
          <div className="space-y-2">
            {splits.splits.map((s) => (
              <div key={s.user_id} className="flex justify-between items-center p-3 bg-cream rounded-xl">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 bg-brand-500 rounded-full flex items-center justify-center font-bold">
                    {s.name[0]}
                  </div>
                  <span className="font-semibold">{s.name}</span>
                </div>
                <span className="font-bold text-lg">₹{s.amount}</span>
              </div>
            ))}
          </div>
        </div>

        <button onClick={() => navigate(`/customer/orders/${splits.order_id}`)} className="btn-primary w-full">
          View Order Details
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <button onClick={() => navigate('/customer')} className="flex items-center gap-1 text-muted">
        <ArrowLeft size={18} /> Home
      </button>

      {/* HERO */}
      <div className="card bg-gradient-to-br from-brand-400 to-brand-500">
        <div className="flex justify-between items-start flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Users size={20} />
              <span className="font-bold text-sm">GROUP ORDER</span>
              {groupInfo.is_host && (
                <span className="bg-dark text-brand-500 px-2 py-0.5 rounded-full text-xs flex items-center gap-1">
                  <Crown size={12} /> HOST
                </span>
              )}
            </div>
            <h1 className="text-2xl font-display font-extrabold">{groupInfo.restaurant.name}</h1>
            <p className="text-sm opacity-80">Host: {groupInfo.host_name}</p>
          </div>

          <div className="text-right">
            <p className="text-xs opacity-80">Share Code</p>
            <p className="text-3xl font-mono font-extrabold tracking-wider">{code}</p>
            <div className="flex gap-2 mt-2">
              <button onClick={copyLink} className="bg-dark text-brand-500 p-2 rounded-lg hover:bg-gray-800">
                <Copy size={16} />
              </button>
              <button onClick={shareWhatsApp} className="bg-dark text-brand-500 p-2 rounded-lg hover:bg-gray-800">
                <Share2 size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* MEMBERS */}
      <div className="card">
        <h3 className="font-bold mb-3 flex items-center gap-2">
          <UserPlus size={18} /> Members ({members.length})
        </h3>
        {members.length === 0 ? (
          <p className="text-muted text-sm">No members yet. Share the code!</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {members.map((m) => (
              <div key={m.user_id} className={`flex items-center gap-2 px-3 py-2 rounded-xl ${m.user_id === user.id ? 'bg-brand-500' : 'bg-cream'}`}>
                <div className="w-8 h-8 bg-dark text-brand-500 rounded-full flex items-center justify-center font-bold text-sm">
                  {m.name[0]}
                </div>
                <div>
                  <p className="text-sm font-bold">{m.name} {m.user_id === user.id && '(you)'}</p>
                  <p className="text-xs">₹{m.subtotal}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* MENU */}
        <div className="lg:col-span-2 card">
          <h3 className="font-bold text-lg mb-3">🍽️ Menu</h3>
          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {menu.map((cat) => (
              <div key={cat.category_id}>
                <h4 className="font-bold text-brand-700 mb-2 sticky top-0 bg-white py-1">{cat.category_name}</h4>
                <div className="space-y-2">
                  {cat.items.map((item) => (
                    <div key={item.id} className="flex items-center gap-3 p-3 bg-cream rounded-xl">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-3 h-3 border ${item.is_veg ? 'border-success' : 'border-danger'}`}>
                            <span className={`block w-full h-full ${item.is_veg ? 'bg-success' : 'bg-danger'}`} style={{ padding: 1 }}></span>
                          </span>
                          <p className="font-semibold text-sm">{item.name}</p>
                        </div>
                        <p className="font-bold">₹{item.price}</p>
                      </div>
                      <button
                        onClick={() => handleAddItem(item)}
                        disabled={!item.is_available}
                        className="btn-primary text-sm py-1 px-3 disabled:opacity-50"
                      >
                        Add
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CART SUMMARY */}
        <div className="lg:col-span-1 space-y-4">
          <div className="card sticky top-24">
            <h3 className="font-bold text-lg mb-3">🛒 Group Cart</h3>

            {items.length === 0 ? (
              <p className="text-muted text-sm text-center py-6">No items yet</p>
            ) : (
              <>
                <div className="space-y-2 max-h-[300px] overflow-y-auto mb-3">
                  {items.map((item) => (
                    <div key={item.id} className={`p-2 rounded-lg ${item.user_id === user.id ? 'bg-brand-100' : 'bg-cream'}`}>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="text-sm font-semibold">{item.name}</p>
                          <p className="text-xs text-muted">by {item.user_name}{item.user_id === user.id && ' (you)'}</p>
                          <p className="text-sm">₹{item.price} × {item.quantity}</p>
                        </div>
                        {item.user_id === user.id && (
                          <button onClick={() => handleRemoveItem(item.id)} className="text-danger p-1">
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t pt-3 space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span className="font-bold">₹{subtotal}</span>
                  </div>
                  <div className="flex justify-between text-muted">
                    <span>Delivery</span>
                    <span>₹30</span>
                  </div>
                  <div className="flex justify-between text-muted">
                    <span>Tax (5%)</span>
                    <span>₹{Math.round(subtotal * 0.05)}</span>
                  </div>
                  <div className="border-t pt-2 flex justify-between font-bold text-lg">
                    <span>Total</span>
                    <span>₹{Math.round(subtotal + 30 + subtotal * 0.05)}</span>
                  </div>
                </div>
              </>
            )}

            {/* HOST ACTIONS */}
            {groupInfo.is_host && items.length > 0 && !showCheckout && (
              <button onClick={() => setShowCheckout(true)} className="btn-primary w-full mt-3">
                Lock & Checkout 🔒
              </button>
            )}

            {!groupInfo.is_host && (
              <p className="text-xs text-center text-muted mt-3">
                Host ({groupInfo.host_name}) will checkout
              </p>
            )}

            {groupInfo.is_host && (
              <button onClick={handleCancel} className="w-full mt-2 text-danger text-sm hover:underline">
                Cancel Group
              </button>
            )}
          </div>
        </div>
      </div>

      {/* CHECKOUT MODAL */}
      {showCheckout && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between mb-4">
              <h3 className="font-bold text-xl">Finalize Group Order</h3>
              <button onClick={() => setShowCheckout(false)}><X /></button>
            </div>

            <div className="mb-4">
              <h4 className="font-bold mb-2">📍 Delivery Address</h4>
              {addresses.length === 0 ? (
                <button onClick={() => navigate('/customer/addresses')} className="btn-secondary w-full">
                  Add Address
                </button>
              ) : (
                <div className="space-y-2">
                  {addresses.map(a => (
                    <label key={a.id} className={`block p-3 rounded-lg border-2 cursor-pointer ${selectedAddress?.id === a.id ? 'border-brand-500 bg-brand-50' : 'border-gray-200'}`}>
                      <input type="radio" checked={selectedAddress?.id === a.id} onChange={() => setSelectedAddress(a)} className="mr-2" />
                      <span className="font-semibold capitalize">{a.label}</span>
                      <p className="text-xs text-muted mt-1">{a.full_address}</p>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="mb-4">
              <h4 className="font-bold mb-2">💳 Payment</h4>
              <div className="space-y-2">
                {[{ v: 'cod', l: 'Cash on Delivery' }, { v: 'razorpay', l: 'Pay Online' }].map(p => (
                  <label key={p.v} className={`block p-3 rounded-lg border-2 cursor-pointer ${paymentMethod === p.v ? 'border-brand-500 bg-brand-50' : 'border-gray-200'}`}>
                    <input type="radio" checked={paymentMethod === p.v} onChange={() => setPaymentMethod(p.v)} className="mr-2" />
                    {p.l}
                  </label>
                ))}
              </div>
            </div>

            <button onClick={handleFinalize} className="btn-primary w-full flex items-center justify-center gap-2">
              <Check size={18} /> Place Order
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
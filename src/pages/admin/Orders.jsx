import { useEffect, useState } from 'react'
import { adminAPI } from '../../api/admin'
import { Loader2, XCircle } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function AdminOrders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('')

  useEffect(() => { load() }, [status])

  const load = async () => {
    setLoading(true)
    try {
      const params = status ? { status } : {}
      const res = await adminAPI.listOrders(params)
      setOrders(res.orders || [])
    } finally { setLoading(false) }
  }

  const handleCancel = async (id) => {
    const reason = prompt('Cancellation reason?')
    if (!reason) return
    try { await adminAPI.cancelOrder(id, reason); toast.success('Cancelled'); load() } catch {}
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">All Orders</h1>

      <div className="flex gap-2 overflow-x-auto">
        {['', 'placed', 'accepted', 'preparing', 'delivered', 'cancelled'].map((s) => (
          <button key={s} onClick={() => setStatus(s)}
            className={`px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap ${status === s ? 'bg-brand-500 text-dark' : 'bg-white text-muted border'}`}>
            {s === '' ? 'All' : s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead className="bg-cream">
              <tr>
                <th className="text-left p-3 text-sm font-bold">Order ID</th>
                <th className="text-left p-3 text-sm font-bold">Customer</th>
                <th className="text-left p-3 text-sm font-bold">Restaurant</th>
                <th className="text-left p-3 text-sm font-bold">Amount</th>
                <th className="text-left p-3 text-sm font-bold">Status</th>
                <th className="text-left p-3 text-sm font-bold">Date</th>
                <th className="text-right p-3 text-sm font-bold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-t hover:bg-cream/50">
                  <td className="p-3 font-mono text-xs">#{o.id.slice(0, 8).toUpperCase()}</td>
                  <td className="p-3 text-sm">{o.customer_name}</td>
                  <td className="p-3 text-sm">{o.restaurant_name}</td>
                  <td className="p-3 font-bold">₹{o.final_amount}</td>
                  <td className="p-3"><StatusBadge status={o.status} /></td>
                  <td className="p-3 text-xs text-muted">{format(new Date(o.placed_at), 'MMM d, h:mm a')}</td>
                  <td className="p-3 text-right">
                    {!['delivered', 'cancelled'].includes(o.status) && (
                      <button onClick={() => handleCancel(o.id)} className="text-danger hover:bg-red-50 p-2 rounded-lg" title="Cancel">
                        <XCircle size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {orders.length === 0 && <p className="text-center py-8 text-muted">No orders found</p>}
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }) {
  const config = {
    placed: 'bg-info/20 text-info',
    accepted: 'bg-brand-200 text-brand-700',
    preparing: 'bg-warning/20 text-warning',
    picked_up: 'bg-warning/20 text-warning',
    out_for_delivery: 'bg-warning/20 text-warning',
    delivered: 'bg-success/20 text-success',
    cancelled: 'bg-danger/20 text-danger',
  }
  return <span className={`text-xs px-2 py-1 rounded font-bold ${config[status] || 'bg-muted/20'}`}>{status?.replace('_', ' ').toUpperCase()}</span>
}
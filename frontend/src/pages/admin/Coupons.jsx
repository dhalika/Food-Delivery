import { useEffect, useState } from 'react'
import { adminAPI } from '../../api/admin'
import { Loader2, Plus, ToggleLeft, ToggleRight, Trash2, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

export default function AdminCoupons() {
  const [coupons, setCoupons] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    code: '', discount_type: 'percentage', discount_value: '',
    max_discount: '', min_order_value: '0', per_user_limit: '1',
    valid_from: '', valid_till: '', description: '',
  })

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const res = await adminAPI.listCoupons()
      setCoupons(res.coupons || [])
    } finally { setLoading(false) }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await adminAPI.createCoupon({
        ...form,
        discount_value: parseFloat(form.discount_value),
        max_discount: form.max_discount ? parseFloat(form.max_discount) : null,
        min_order_value: parseFloat(form.min_order_value),
        per_user_limit: parseInt(form.per_user_limit),
        valid_from: new Date(form.valid_from).toISOString(),
        valid_till: new Date(form.valid_till).toISOString(),
      })
      toast.success('Coupon created!')
      setShowForm(false)
      setForm({ code: '', discount_type: 'percentage', discount_value: '', max_discount: '', min_order_value: '0', per_user_limit: '1', valid_from: '', valid_till: '', description: '' })
      load()
    } catch {}
  }

  const handleToggle = async (id) => {
    try { await adminAPI.toggleCoupon(id); load() } catch {}
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this coupon?')) return
    try { await adminAPI.deleteCoupon(id); toast.success('Deleted'); load() } catch {}
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between">
        <h1 className="text-3xl font-display font-bold">Coupons</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> New Coupon
        </button>
      </div>

      {showForm && (
        <div className="card">
          <div className="flex justify-between mb-3">
            <h3 className="font-bold text-lg">Create Coupon</h3>
            <button onClick={() => setShowForm(false)}><X /></button>
          </div>
          <form onSubmit={handleCreate} className="grid grid-cols-2 gap-3">
            <input required placeholder="Code (e.g. SAVE20)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="input-field" />
            <select value={form.discount_type} onChange={(e) => setForm({ ...form, discount_type: e.target.value })} className="input-field">
              <option value="percentage">Percentage %</option>
              <option value="flat">Flat ₹</option>
            </select>
            <input required type="number" placeholder="Discount Value" value={form.discount_value} onChange={(e) => setForm({ ...form, discount_value: e.target.value })} className="input-field" />
            <input type="number" placeholder="Max Discount (cap)" value={form.max_discount} onChange={(e) => setForm({ ...form, max_discount: e.target.value })} className="input-field" />
            <input type="number" placeholder="Min Order Value" value={form.min_order_value} onChange={(e) => setForm({ ...form, min_order_value: e.target.value })} className="input-field" />
            <input type="number" placeholder="Per User Limit" value={form.per_user_limit} onChange={(e) => setForm({ ...form, per_user_limit: e.target.value })} className="input-field" />
            <input required type="datetime-local" value={form.valid_from} onChange={(e) => setForm({ ...form, valid_from: e.target.value })} className="input-field" />
            <input required type="datetime-local" value={form.valid_till} onChange={(e) => setForm({ ...form, valid_till: e.target.value })} className="input-field" />
            <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input-field col-span-2" />
            <button type="submit" className="btn-primary col-span-2">Create Coupon</button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>
      ) : (
        <div className="space-y-3">
          {coupons.map((c) => (
            <div key={c.id} className="card flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="font-bold text-xl font-mono bg-brand-100 text-brand-700 px-3 py-1 rounded">{c.code}</span>
                  {c.is_active ? (
                    <span className="text-xs bg-success/20 text-success px-2 py-1 rounded">ACTIVE</span>
                  ) : (
                    <span className="text-xs bg-danger/20 text-danger px-2 py-1 rounded">INACTIVE</span>
                  )}
                </div>
                <p className="text-sm text-muted">{c.description}</p>
                <p className="text-xs text-muted mt-1">
                  {c.discount_type === 'percentage' ? `${c.discount_value}% off` : `₹${c.discount_value} off`}
                  {c.max_discount && ` (max ₹${c.max_discount})`}
                  • Min ₹{c.min_order_value}
                  • Used {c.used_count}x
                </p>
                <p className="text-xs text-muted">Valid till {format(new Date(c.valid_till), 'MMM d, yyyy')}</p>
              </div>
              <div className="flex gap-1">
                <button onClick={() => handleToggle(c.id)} className={c.is_active ? 'text-success' : 'text-muted'}>
                  {c.is_active ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
                </button>
                <button onClick={() => handleDelete(c.id)} className="p-2 text-danger hover:bg-red-50 rounded">
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
import { useState, useEffect } from 'react'
import { customerAPI } from '../../api/customer'
import { MapPin, Plus, Trash2, Home, Briefcase, Loader2, X } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Addresses({ selectMode = false, onSelect }) {
  const [addresses, setAddresses] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    label: 'home', full_address: '', city: '', state: '', pincode: '', is_default: false,
  })

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const res = await customerAPI.listAddresses()
      setAddresses(res.addresses || [])
    } finally { setLoading(false) }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    try {
      await customerAPI.addAddress(form)
      toast.success('Address added')
      setShowForm(false)
      setForm({ label: 'home', full_address: '', city: '', state: '', pincode: '', is_default: false })
      load()
    } catch {}
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this address?')) return
    try {
      await customerAPI.deleteAddress(id)
      toast.success('Deleted')
      load()
    } catch {}
  }

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>

  return (
    <div className="space-y-4">
      {!selectMode && <h1 className="text-3xl font-display font-bold">My Addresses</h1>}

      {addresses.length === 0 && !showForm && (
        <div className="card text-center py-12">
          <MapPin size={48} className="mx-auto text-muted mb-3" />
          <h3 className="font-bold mb-1">No addresses yet</h3>
          <p className="text-muted text-sm mb-4">Add your first delivery address</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {addresses.map((addr) => (
          <div key={addr.id} className={`card hover:shadow-brand cursor-pointer ${selectMode ? 'hover:border-2 hover:border-brand-500' : ''}`}
            onClick={() => selectMode && onSelect(addr)}>
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-2">
                {addr.label === 'home' ? <Home size={18} className="text-brand-600" /> : <Briefcase size={18} className="text-brand-600" />}
                <span className="font-bold capitalize">{addr.label}</span>
                {addr.is_default && <span className="text-xs bg-brand-500 text-dark px-2 py-0.5 rounded-full">Default</span>}
              </div>
              {!selectMode && (
                <button onClick={(e) => { e.stopPropagation(); handleDelete(addr.id) }} className="text-danger hover:bg-red-50 p-1 rounded">
                  <Trash2 size={16} />
                </button>
              )}
            </div>
            <p className="text-sm mt-2">{addr.full_address}</p>
            <p className="text-sm text-muted">{addr.city}, {addr.state} - {addr.pincode}</p>
          </div>
        ))}
      </div>

      {!showForm ? (
        <button onClick={() => setShowForm(true)} className="btn-secondary flex items-center gap-2">
          <Plus size={18} /> Add New Address
        </button>
      ) : (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold">New Address</h3>
            <button onClick={() => setShowForm(false)}><X size={20} /></button>
          </div>
          <form onSubmit={handleSave} className="space-y-3">
            <div className="flex gap-2">
              {['home', 'work', 'other'].map((l) => (
                <button type="button" key={l} onClick={() => setForm({ ...form, label: l })}
                  className={`px-4 py-2 rounded-xl capitalize font-semibold text-sm ${form.label === l ? 'bg-brand-500 text-dark' : 'bg-cream text-muted'}`}>
                  {l}
                </button>
              ))}
            </div>
            <input required placeholder="Full address" value={form.full_address}
              onChange={(e) => setForm({ ...form, full_address: e.target.value })} className="input-field" />
            <div className="grid grid-cols-2 gap-3">
              <input required placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="input-field" />
              <input required placeholder="State" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} className="input-field" />
            </div>
            <input required placeholder="Pincode" value={form.pincode} onChange={(e) => setForm({ ...form, pincode: e.target.value })} className="input-field" />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} />
              Set as default
            </label>
            <button type="submit" className="btn-primary w-full">Save Address</button>
          </form>
        </div>
      )}
    </div>
  )
}
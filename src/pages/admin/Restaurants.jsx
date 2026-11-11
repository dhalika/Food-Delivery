import { useEffect, useState } from 'react'
import { adminAPI } from '../../api/admin'
import { Loader2, CheckCircle, XCircle, Trash2, Store } from 'lucide-react'
import toast from 'react-hot-toast'

export default function AdminRestaurants() {
  const [restaurants, setRestaurants] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => { load() }, [filter])

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filter === 'pending') params.is_verified = 'false'
      if (filter === 'verified') params.is_verified = 'true'
      const res = await adminAPI.listRestaurants(params)
      setRestaurants(res.restaurants || [])
    } finally { setLoading(false) }
  }

  const handleVerify = async (id) => {
    try {
      const res = await adminAPI.verifyRestaurant(id)
      toast.success(res.message)
      load()
    } catch {}
  }

  const handleToggle = async (id) => {
    try { await adminAPI.toggleRestaurant(id); toast.success('Toggled'); load() } catch {}
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this restaurant? This cannot be undone.')) return
    try { await adminAPI.deleteRestaurant(id); toast.success('Deleted'); load() } catch {}
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">Restaurant Management</h1>

      <div className="flex gap-2">
        {['', 'pending', 'verified'].map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-full text-sm font-semibold ${filter === f ? 'bg-brand-500 text-dark' : 'bg-white text-muted border'}`}>
            {f === '' ? 'All' : f === 'pending' ? 'Pending Verification' : 'Verified'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {restaurants.map((r) => (
            <div key={r.id} className="card">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-bold text-lg">{r.name}</h3>
                  <p className="text-sm text-muted">{r.cuisine_type}</p>
                  <p className="text-xs text-muted">{r.city}</p>
                </div>
                <div className="flex flex-col gap-1 items-end">
                  {r.is_verified ? (
                    <span className="text-xs bg-success/20 text-success px-2 py-1 rounded">✓ Verified</span>
                  ) : (
                    <span className="text-xs bg-warning/20 text-warning px-2 py-1 rounded">Pending</span>
                  )}
                  {r.is_active ? (
                    <span className="text-xs bg-info/20 text-info px-2 py-1 rounded">Active</span>
                  ) : (
                    <span className="text-xs bg-danger/20 text-danger px-2 py-1 rounded">Inactive</span>
                  )}
                </div>
              </div>

              <div className="text-sm text-muted mb-3 border-t pt-2">
                <p>👤 Owner: {r.owner_name}</p>
                <p>📧 {r.owner_email}</p>
                <p>⭐ {r.avg_rating} ({r.total_reviews} reviews)</p>
              </div>

              <div className="flex gap-2">
                <button onClick={() => handleVerify(r.id)} className={`flex-1 text-sm py-2 rounded-xl font-semibold flex items-center justify-center gap-1 ${r.is_verified ? 'bg-muted/20 text-muted' : 'bg-success text-white'}`}>
                  {r.is_verified ? <><XCircle size={14} /> Unverify</> : <><CheckCircle size={14} /> Verify</>}
                </button>
                <button onClick={() => handleToggle(r.id)} className="text-sm px-3 py-2 bg-cream hover:bg-brand-100 rounded-xl font-semibold">
                  Toggle
                </button>
                <button onClick={() => handleDelete(r.id)} className="p-2 text-danger hover:bg-red-50 rounded-xl">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
import { useEffect, useState } from 'react'
import { restaurantAPI } from '../../api/restaurant'
import { useRestaurantStore } from '../../store/restaurantStore'
import { Store, Loader2, Save, ToggleRight, ToggleLeft } from 'lucide-react'
import toast from 'react-hot-toast'

export default function RestaurantProfile() {
  const { selectedRestaurant, setRestaurant } = useRestaurantStore()
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (selectedRestaurant) {
      setForm({
        name: selectedRestaurant.name || '',
        description: selectedRestaurant.description || '',
        cuisine_type: selectedRestaurant.cuisine_type || '',
        phone: selectedRestaurant.phone || '',
        min_order_value: selectedRestaurant.min_order_value || 0,
      })
    }
  }, [selectedRestaurant])

  const handleSave = async () => {
    setSaving(true)
    try {
      await restaurantAPI.update(selectedRestaurant.id, form)
      setRestaurant({ ...selectedRestaurant, ...form })
      toast.success('Restaurant updated!')
    } catch {} finally {
      setSaving(false)
    }
  }

  const handleToggle = async () => {
    try {
      const res = await restaurantAPI.toggleActive(selectedRestaurant.id)
      setRestaurant({ ...selectedRestaurant, is_active: res.is_active })
      toast.success(res.is_active ? 'Restaurant is now OPEN' : 'Restaurant CLOSED')
    } catch {}
  }

  if (!selectedRestaurant) return <div className="card text-center">No restaurant selected</div>

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-3xl font-display font-bold flex items-center gap-2">
        <Store /> Restaurant Profile
      </h1>

      <div className="card flex items-center justify-between">
        <div>
          <p className="font-semibold">Accept Orders</p>
          <p className="text-sm text-muted">Toggle to stop accepting orders temporarily</p>
        </div>
        <button onClick={handleToggle} className={selectedRestaurant.is_active ? 'text-success' : 'text-muted'}>
          {selectedRestaurant.is_active ? <ToggleRight size={48} /> : <ToggleLeft size={48} />}
        </button>
      </div>

      <div className="card space-y-4">
        <h3 className="font-bold text-lg">Basic Info</h3>
        <Field label="Restaurant Name">
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" />
        </Field>
        <Field label="Description">
          <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="input-field resize-none" />
        </Field>
        <Field label="Cuisine Type">
          <input value={form.cuisine_type} onChange={(e) => setForm({ ...form, cuisine_type: e.target.value })} className="input-field" placeholder="e.g. Pizza, Italian" />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Phone">
            <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input-field" />
          </Field>
          <Field label="Min Order Value (₹)">
            <input type="number" value={form.min_order_value} onChange={(e) => setForm({ ...form, min_order_value: parseFloat(e.target.value) })} className="input-field" />
          </Field>
        </div>

        <button onClick={handleSave} disabled={saving} className="btn-primary w-full flex items-center justify-center gap-2">
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save Changes
        </button>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="text-sm font-semibold text-muted">{label}</label>
      <div className="mt-1">{children}</div>
    </div>
  )
}
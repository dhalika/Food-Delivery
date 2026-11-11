import { useEffect, useState } from 'react'
import { restaurantAPI } from '../../api/restaurant'
import { useRestaurantStore } from '../../store/restaurantStore'
import { Loader2, Clock, Save } from 'lucide-react'
import toast from 'react-hot-toast'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function Timings() {
  const { selectedRestaurant } = useRestaurantStore()
  const [timings, setTimings] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => { if (selectedRestaurant) load() }, [selectedRestaurant])

  const load = async () => {
    try {
      const res = await restaurantAPI.getTimings(selectedRestaurant.id)
      const existing = res.timings || []
      const full = DAYS.map((_, i) => {
        const found = existing.find(t => t.day === i)
        return found || { day: i, opening_time: '09:00:00', closing_time: '22:00:00', is_closed: false }
      })
      setTimings(full)
    } finally { setLoading(false) }
  }

  const handleChange = (day, field, value) => {
    setTimings(timings.map(t => t.day === day ? { ...t, [field]: value } : t))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = timings.map(t => ({
        day: t.day,
        opening: t.opening_time?.slice(0, 5) || '00:00',
        closing: t.closing_time?.slice(0, 5) || '00:00',
        is_closed: t.is_closed,
      }))
      await restaurantAPI.setTimings(selectedRestaurant.id, payload)
      toast.success('Timings saved!')
    } catch {} finally {
      setSaving(false)
    }
  }

  if (!selectedRestaurant) return <div className="card text-center">Select a restaurant first</div>
  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-3xl font-display font-bold flex items-center gap-2">
        <Clock /> Restaurant Timings
      </h1>

      <div className="card space-y-3">
        {timings.map((t) => (
          <div key={t.day} className="flex items-center gap-4 pb-3 border-b last:border-0 last:pb-0">
            <div className="w-28 font-semibold">{DAYS[t.day]}</div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!t.is_closed} onChange={(e) => handleChange(t.day, 'is_closed', !e.target.checked)} />
              Open
            </label>
            {!t.is_closed ? (
              <>
                <input
                  type="time"
                  value={t.opening_time?.slice(0, 5)}
                  onChange={(e) => handleChange(t.day, 'opening_time', e.target.value + ':00')}
                  className="input-field w-auto"
                />
                <span>to</span>
                <input
                  type="time"
                  value={t.closing_time?.slice(0, 5)}
                  onChange={(e) => handleChange(t.day, 'closing_time', e.target.value + ':00')}
                  className="input-field w-auto"
                />
              </>
            ) : (
              <span className="text-muted font-semibold">Closed</span>
            )}
          </div>
        ))}
      </div>

      <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
        {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
        Save Timings
      </button>
    </div>
  )
}
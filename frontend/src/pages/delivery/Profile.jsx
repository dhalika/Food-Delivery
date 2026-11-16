import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'
import { customerAPI } from '../../api/customer'
import { User, Mail, Phone, Edit, Save, Loader2, LogOut } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../../hooks/useAuth'

export default function DeliveryProfile() {
  const { user, updateUser } = useAuthStore()
  const { logout } = useAuth()
  const [editMode, setEditMode] = useState(false)
  const [form, setForm] = useState({ name: user?.name || '', phone: user?.phone || '' })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await customerAPI.updateProfile(form)
      updateUser({ ...user, ...form })
      toast.success('Profile updated!')
      setEditMode(false)
    } catch {} finally { setSaving(false) }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-display font-bold">My Profile</h1>

      <div className="card text-center">
        <div className="w-24 h-24 mx-auto bg-gradient-to-br from-brand-400 to-brand-600 rounded-full flex items-center justify-center text-5xl">
          🛵
        </div>
        <h2 className="text-2xl font-display font-bold mt-3">{user?.name}</h2>
        <p className="text-muted text-sm">Delivery Partner</p>
      </div>

      <div className="card">
        <div className="flex justify-between mb-4">
          <h3 className="font-bold text-lg">Personal Info</h3>
          {!editMode ? (
            <button onClick={() => setEditMode(true)} className="text-brand-600 flex items-center gap-1 font-semibold">
              <Edit size={16} /> Edit
            </button>
          ) : (
            <button onClick={() => { setEditMode(false); setForm({ name: user.name, phone: user.phone }) }} className="text-muted">
              Cancel
            </button>
          )}
        </div>

        <div className="space-y-3">
          <Field icon={<User size={18} />} label="Name">
            {editMode ? (
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" />
            ) : <p className="font-semibold">{user?.name}</p>}
          </Field>

          <Field icon={<Mail size={18} />} label="Email">
            <p className="font-semibold">{user?.email}</p>
          </Field>

          <Field icon={<Phone size={18} />} label="Phone">
            {editMode ? (
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input-field" />
            ) : <p className="font-semibold">{user?.phone}</p>}
          </Field>
        </div>

        {editMode && (
          <button onClick={handleSave} disabled={saving} className="btn-primary w-full mt-4 flex items-center justify-center gap-2">
            {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
            Save
          </button>
        )}
      </div>

      <button onClick={logout} className="w-full card flex items-center justify-center gap-2 text-danger font-semibold">
        <LogOut size={18} /> Logout
      </button>
    </div>
  )
}

function Field({ icon, label, children }) {
  return (
    <div className="flex items-start gap-3 pb-3 border-b last:border-0">
      <div className="text-brand-600 mt-1">{icon}</div>
      <div className="flex-1">
        <p className="text-xs text-muted">{label}</p>
        {children}
      </div>
    </div>
  )
}
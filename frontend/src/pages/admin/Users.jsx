import { useEffect, useState } from 'react'
import { adminAPI } from '../../api/admin'
import { Loader2, Ban, CheckCircle, Trash2, Search } from 'lucide-react'
import toast from 'react-hot-toast'

export default function AdminUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [role, setRole] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => { load() }, [role, search])

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      if (role) params.role = role
      if (search) params.search = search
      const res = await adminAPI.listUsers(params)
      setUsers(res.users || [])
    } finally { setLoading(false) }
  }

  const handleBlock = async (id) => {
    try {
      const res = await adminAPI.blockUser(id)
      toast.success(res.message)
      load()
    } catch {}
  }

  const handleDelete = async (id) => {
    if (!confirm('Permanently delete this user?')) return
    try {
      await adminAPI.deleteUser(id)
      toast.success('User deleted')
      load()
    } catch {}
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">User Management</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-64">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name, email, phone..." className="input-field pl-10" />
        </div>
        <select value={role} onChange={(e) => setRole(e.target.value)} className="input-field w-auto">
          <option value="">All Roles</option>
          <option value="customer">Customer</option>
          <option value="restaurant_owner">Restaurant Owner</option>
          <option value="delivery_partner">Delivery Partner</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead className="bg-cream">
              <tr>
                <th className="text-left p-3 text-sm font-bold">Name</th>
                <th className="text-left p-3 text-sm font-bold">Email</th>
                <th className="text-left p-3 text-sm font-bold">Phone</th>
                <th className="text-left p-3 text-sm font-bold">Role</th>
                <th className="text-left p-3 text-sm font-bold">Status</th>
                <th className="text-right p-3 text-sm font-bold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t hover:bg-cream/50">
                  <td className="p-3 font-semibold">{u.name}</td>
                  <td className="p-3 text-sm">{u.email}</td>
                  <td className="p-3 text-sm">{u.phone}</td>
                  <td className="p-3">
                    <span className="text-xs bg-brand-100 text-brand-700 px-2 py-1 rounded capitalize">
                      {u.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="p-3">
                    {u.is_active ? (
                      <span className="text-xs bg-success/20 text-success px-2 py-1 rounded">Active</span>
                    ) : (
                      <span className="text-xs bg-danger/20 text-danger px-2 py-1 rounded">Blocked</span>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <button onClick={() => handleBlock(u.id)} className={`p-2 rounded-lg mr-1 ${u.is_active ? 'text-danger hover:bg-red-50' : 'text-success hover:bg-green-50'}`} title={u.is_active ? 'Block' : 'Unblock'}>
                      {u.is_active ? <Ban size={16} /> : <CheckCircle size={16} />}
                    </button>
                    <button onClick={() => handleDelete(u.id)} className="p-2 text-danger hover:bg-red-50 rounded-lg">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users.length === 0 && <p className="text-center py-8 text-muted">No users found</p>}
        </div>
      )}
    </div>
  )
}
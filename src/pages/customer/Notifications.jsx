import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { customerAPI } from '../../api/customer'
import { Bell, Package, Tag, Info, Check, Trash2, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import toast from 'react-hot-toast'

const TYPE_CONFIG = {
  order_update: { icon: <Package />, color: 'bg-info/20 text-info' },
  promotion: { icon: <Tag />, color: 'bg-brand-200 text-brand-700' },
  system: { icon: <Info />, color: 'bg-muted/20 text-muted' },
}

export default function Notifications() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [unreadOnly, setUnreadOnly] = useState(false)

  useEffect(() => { load() }, [unreadOnly])

  const load = async () => {
    setLoading(true)
    try {
      const res = await customerAPI.getNotifications({ unread_only: unreadOnly })
      setNotifications(res.notifications || [])
    } finally { setLoading(false) }
  }

  const handleRead = async (id) => {
    try { await customerAPI.markRead(id); load() } catch {}
  }

  const handleAllRead = async () => {
    try {
      await customerAPI.markAllRead()
      toast.success('All marked as read')
      load()
    } catch {}
  }

  const handleDelete = async (id) => {
    try { await customerAPI.deleteNotification(id); load() } catch {}
  }

  const handleClick = (n) => {
    if (!n.is_read) handleRead(n.id)
    if (n.type === 'order_update' && n.reference_id) {
      navigate(`/customer/orders/${n.reference_id}`)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-display font-bold">Notifications</h1>
        <button onClick={handleAllRead} className="text-brand-600 font-semibold text-sm hover:underline flex items-center gap-1">
          <Check size={14} /> Mark all read
        </button>
      </div>

      <div className="flex gap-2">
        <button onClick={() => setUnreadOnly(false)}
          className={`px-4 py-2 rounded-full text-sm font-semibold ${!unreadOnly ? 'bg-brand-500 text-dark' : 'bg-white text-muted border'}`}>
          All
        </button>
        <button onClick={() => setUnreadOnly(true)}
          className={`px-4 py-2 rounded-full text-sm font-semibold ${unreadOnly ? 'bg-brand-500 text-dark' : 'bg-white text-muted border'}`}>
          Unread
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>
      ) : notifications.length === 0 ? (
        <div className="card text-center py-12">
          <Bell size={48} className="mx-auto text-muted mb-3" />
          <h3 className="text-xl font-bold mb-1">No notifications</h3>
          <p className="text-muted">You're all caught up!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => {
            const type = TYPE_CONFIG[n.type] || TYPE_CONFIG.system
            return (
              <div key={n.id}
                className={`card flex items-start gap-3 cursor-pointer hover:shadow-brand transition ${!n.is_read ? 'border-l-4 border-brand-500 bg-brand-50' : ''}`}
                onClick={() => handleClick(n)}>
                <div className={`p-2 rounded-lg ${type.color}`}>{type.icon}</div>
                <div className="flex-1">
                  <h4 className="font-bold">{n.title}</h4>
                  <p className="text-sm text-muted">{n.message}</p>
                  <p className="text-xs text-muted mt-1">
                    {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                  </p>
                </div>
                <button onClick={(e) => { e.stopPropagation(); handleDelete(n.id) }}
                  className="text-muted hover:text-danger p-1">
                  <Trash2 size={16} />
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
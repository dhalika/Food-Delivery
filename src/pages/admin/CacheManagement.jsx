import { useEffect, useState } from 'react'
import { adminAPI } from '../../api/admin'
import { Loader2, Database, Trash2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function CacheManagement() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const res = await adminAPI.cacheStats()
      setStats(res)
    } catch {} finally { setLoading(false) }
  }

  const handleClear = async () => {
    if (!confirm('Clear ALL cache? Users may see slower responses temporarily.')) return
    try {
      await adminAPI.clearCache()
      toast.success('Cache cleared!')
      load()
    } catch {}
  }

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold flex items-center gap-2">
        <Database /> Cache Management
      </h1>

      {stats?.error ? (
        <div className="card bg-danger/10 border border-danger/30">
          <p className="text-danger">Redis cache unavailable: {stats.error}</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Stat title="Memory Used" value={stats?.used_memory_human || 'N/A'} />
            <Stat title="Total Keys" value={stats?.total_keys || 0} />
            <Stat title="Connected Clients" value={stats?.connected_clients || 0} />
            <Stat title="Hit Rate" value={`${stats?.hit_rate || 0}%`} color="text-success" />
          </div>

          <div className="card">
            <h3 className="font-bold text-lg mb-3">Cache Statistics</h3>
            <div className="space-y-2 text-sm">
              <Row label="Keyspace Hits" value={stats?.keyspace_hits?.toLocaleString() || 0} />
              <Row label="Keyspace Misses" value={stats?.keyspace_misses?.toLocaleString() || 0} />
              <Row label="Uptime" value={`${Math.floor((stats?.uptime_seconds || 0) / 3600)} hours`} />
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={load} className="btn-secondary flex items-center gap-2">
              <RefreshCw size={16} /> Refresh
            </button>
            <button onClick={handleClear} className="bg-danger text-white px-4 py-2 rounded-xl font-semibold flex items-center gap-2 hover:bg-red-600">
              <Trash2 size={16} /> Clear All Cache
            </button>
          </div>
        </>
      )}
    </div>
  )
}

function Stat({ title, value, color = 'text-dark' }) {
  return (
    <div className="card">
      <p className="text-xs text-muted">{title}</p>
      <p className={`text-2xl font-display font-extrabold mt-1 ${color}`}>{value}</p>
    </div>
  )
}

function Row({ label, value }) {
  return <div className="flex justify-between"><span className="text-muted">{label}</span><span className="font-semibold">{value}</span></div>
}
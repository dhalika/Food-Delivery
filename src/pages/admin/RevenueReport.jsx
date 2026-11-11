import { useState } from 'react'
import { adminAPI } from '../../api/admin'
import { Loader2, TrendingUp, Calendar } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts'

export default function RevenueReport() {
  const [from, setFrom] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0])
  const [to, setTo] = useState(new Date().toISOString().split('T')[0])
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const res = await adminAPI.revenueReport(from, to)
      setReport(res)
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold">Revenue Reports</h1>

      <div className="card flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-muted">From Date</label>
          <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="input-field" />
        </div>
        <div>
          <label className="text-xs text-muted">To Date</label>
          <input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="input-field" />
        </div>
        <button onClick={generate} disabled={loading} className="btn-primary">
          {loading ? <Loader2 className="animate-spin" size={18} /> : 'Generate'}
        </button>
      </div>

      {report && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat title="Total Revenue" value={`₹${report.total_revenue?.toLocaleString()}`} />
            <Stat title="Total Orders" value={report.total_orders} />
            <Stat title="Avg Order Value" value={`₹${report.avg_order_value}`} />
            <Stat title="Discounts Given" value={`₹${report.total_discounts}`} color="text-danger" />
          </div>

          <div className="card">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <TrendingUp /> Daily Revenue
            </h3>
            {report.daily_breakdown?.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={report.daily_breakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Area type="monotone" dataKey="revenue" stroke="#FFC72C" fill="#FFE485" strokeWidth={3} />
                </AreaChart>
              </ResponsiveContainer>
            ) : <p className="text-center text-muted py-8">No data for this range</p>}
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
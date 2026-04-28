import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboardStats, getDashboardHistory, deleteAssessment } from '../api/client'
import Navbar    from '../components/Navbar'
import RiskBadge from '../components/RiskBadge'
import {
  Users, AlertTriangle, TrendingUp, Activity,
  ChevronRight, RefreshCw, Trash2,
  ChevronLeft, ChevronsLeft, ChevronsRight
} from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis
} from 'recharts'

const PAGE_SIZE = 10

const StatCard = ({ label, value, sub, icon, accent }) => {
  const Icon = icon
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${accent}`}>
          <Icon size={16} className="text-white" />
        </div>
      </div>
      <p className="text-2xl font-display text-snow">{value ?? '—'}</p>
      <p className="text-xs text-ghost mt-1">{label}</p>
      {sub && <p className="text-xs text-muted mt-0.5">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const navigate             = useNavigate()
  const [stats,   setStats]  = useState(null)
  const [history, setHistory]= useState([])
  const [loading, setLoading]= useState(true)
  const [page,    setPage]   = useState(1)


  useEffect(() => {
      let mounted = true;
      (async () => {
        try {
          const [s, h] = await Promise.all([
            getDashboardStats(),
            getDashboardHistory(),
          ]);
          if (mounted) {
            setStats(s.data);
            setHistory(h.data.records || []);
            setLoading(false);
          }
        } catch {
          if (mounted) setLoading(false);
        }
      })();
      return () => {
        mounted = false;
      };
    }, []);

  // const load = useCallback(async () => {
  //   setLoading(true)
  //   try {
  //     const [s, h] = await Promise.all([
  //       getDashboardStats(),
  //       getDashboardHistory(),
  //     ])
  //     setStats(s.data)
  //     setHistory(h.data.records || [])
  //   } catch {}
  //   finally { setLoading(false) }
  // }, [])

  // useEffect(() => { load() }, [load])

  // ── Pagination logic ──────────────────────────────────────
  const totalPages  = Math.ceil(history.length / PAGE_SIZE)
  const paginated   = history.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const goTo    = (p) => setPage(Math.max(1, Math.min(p, totalPages)))

  const pieData = stats ? [
    { name: 'High',   value: stats.high_risk,  color: '#EF4444' },
    { name: 'Medium', value: stats.medium_risk, color: '#F59E0B' },
    { name: 'Low',    value: stats.low_risk,    color: '#10B981' },
  ] : []

  const catData = stats?.top_categories?.map(c => ({
    name : c.category.length > 14 ? c.category.slice(0, 14) + '…' : c.category,
    count: c.count,
  })) || [];


  const load = useCallback(async () => {
      setLoading(true);
      try {
        const [s, h] = await Promise.all([
          getDashboardStats(),
          getDashboardHistory(),
        ]);
        setStats(s.data);
        setHistory(h.data.records || []);
      } catch {
        // Error handled silently
      } finally {
        setLoading(false);
      }
    }, []);

  return (
    <div className="flex min-h-screen bg-ink">
      <Navbar />

      <main className="ml-56 flex-1 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-2xl text-snow">Dashboard</h1>
            <p className="text-sm text-muted mt-0.5">Overview of student risk assessments</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={load} className="btn-ghost flex items-center gap-2 text-sm">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
            <button onClick={() => navigate('/upload')} className="btn-primary text-sm">
              New Assessment
            </button>
          </div>
        </div>

        {loading && !stats ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <StatCard label="Total Assessed"   value={stats?.total_assessed} icon={Users}         accent="bg-accent" />
              <StatCard label="At-Risk Students" value={stats?.at_risk_count}  icon={AlertTriangle}  accent="bg-red-500" />
              <StatCard label="Avg Risk Score"   value={stats?.avg_risk_score ? `${stats.avg_risk_score}%` : '—'} icon={TrendingUp} accent="bg-amber-500" />
              <StatCard label="High Risk"        value={stats?.high_risk}      icon={Activity}       accent="bg-rose-600" />
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              {/* Pie */}
              <div className="card p-5">
                <h2 className="text-sm font-medium text-ghost mb-4">Risk Distribution</h2>
                {stats?.total_assessed ? (
                  <div className="flex items-center gap-6">
                    <ResponsiveContainer width={140} height={140}>
                      <PieChart>
                        <Pie data={pieData} cx="50%" cy="50%"
                             innerRadius={42} outerRadius={62}
                             dataKey="value" strokeWidth={0}>
                          {pieData.map((d, i) => (
                            <Cell key={i} fill={d.color} fillOpacity={0.9} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: '#21262F', border: '1px solid #2E333D', borderRadius: 8, fontSize: 12 }}
                          itemStyle={{ color: '#F4F5F7' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-2">
                      {pieData.map(d => (
                        <div key={d.name} className="flex items-center gap-2 text-sm">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                          <span className="text-ghost">{d.name}</span>
                          <span className="font-mono text-snow ml-auto">{d.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted text-center py-10">No data yet</p>
                )}
              </div>

              {/* Top categories */}
              <div className="card p-5">
                <h2 className="text-sm font-medium text-ghost mb-4">Top Intervention Areas</h2>
                {catData.length ? (
                  <ResponsiveContainer width="100%" height={140}>
                    <BarChart data={catData} layout="vertical" margin={{ left: 8, right: 16 }}>
                      <XAxis type="number" hide />
                      <YAxis type="category" dataKey="name" width={100}
                             tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: '#21262F', border: '1px solid #2E333D', borderRadius: 8, fontSize: 12 }}
                        itemStyle={{ color: '#F4F5F7' }}
                        cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                      />
                      <Bar dataKey="count" fill="#6366F1" fillOpacity={0.8}
                           radius={[0, 4, 4, 0]} maxBarSize={14} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-muted text-center py-10">No data yet</p>
                )}
              </div>
            </div>

            {/* Recent assessments table with pagination */}
            <div className="card">
              {/* Table header */}
              <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <h2 className="text-sm font-medium text-ghost">
                  Recent Assessments
                  {history.length > 0 && (
                    <span className="ml-2 text-muted font-normal">
                      ({history.length} total)
                    </span>
                  )}
                </h2>
                {totalPages > 1 && (
                  <span className="text-xs text-muted">
                    Page {page} of {totalPages}
                  </span>
                )}
              </div>

              {history.length === 0 ? (
                <div className="p-8 text-center">
                  <p className="text-sm text-muted">No assessments yet.</p>
                  <button onClick={() => navigate('/upload')}
                          className="btn-primary text-sm mt-3">
                    Upload your first batch
                  </button>
                </div>
              ) : (
                <>
                  {/* Rows */}
                  <div className="divide-y divide-border">
                    {paginated.map((r) => (
                      <div key={r.id}
                           className="flex items-center justify-between px-5 py-3
                                      hover:bg-white/2 transition-colors group">
                        <div className="flex items-center gap-4 flex-1 cursor-pointer"
                             onClick={() => navigate(`/student/${r.student_id}`)}>
                          <div>
                            <p className="text-sm font-medium text-snow">{r.student_id}</p>
                            <p className="text-xs text-muted font-mono">{r.batch_id}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <RiskBadge band={r.risk_band} score={r.risk_score} />
                          <span className="text-xs text-muted w-20 text-right">
                            {new Date(r.created_at).toLocaleDateString()}
                          </span>
                          <button
                            onClick={async (e) => {
                              e.stopPropagation()
                              if (!window.confirm(`Delete assessment for ${r.student_id}?`)) return
                              try {
                                await deleteAssessment(r.id)
                                const updated = history.filter(x => x.id !== r.id)
                                setHistory(updated)
                                // If page is now empty go back one
                                const newTotal = Math.ceil(updated.length / PAGE_SIZE)
                                if (page > newTotal && newTotal > 0) setPage(newTotal)
                              } catch (err) {
                              console.error(err);
                              }
                            }}
                            className="opacity-0 group-hover:opacity-100 transition-opacity
                                       p-1.5 rounded-md hover:bg-red-500/10 text-muted hover:text-red-400"
                            title="Delete assessment"
                          >
                            <Trash2 size={13} />
                          </button>
                          <ChevronRight
                            size={14}
                            className="text-muted cursor-pointer"
                            onClick={() => navigate(`/student/${r.student_id}`)}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Pagination controls */}
                  {totalPages > 1 && (
                    <div className="px-5 py-3 border-t border-border flex items-center justify-between">
                      <span className="text-xs text-muted">
                        Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, history.length)} of {history.length}
                      </span>
                      <div className="flex items-center gap-1">
                        {/* First page */}
                        <button
                          onClick={() => goTo(1)}
                          disabled={page === 1}
                          className="p-1.5 rounded-md text-ghost hover:text-snow hover:bg-white/5
                                     disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                          title="First page"
                        >
                          <ChevronsLeft size={14} />
                        </button>
                        {/* Prev */}
                        <button
                          onClick={() => goTo(page - 1)}
                          disabled={page === 1}
                          className="p-1.5 rounded-md text-ghost hover:text-snow hover:bg-white/5
                                     disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                          title="Previous page"
                        >
                          <ChevronLeft size={14} />
                        </button>

                        {/* Page numbers */}
                        {Array.from({ length: totalPages }, (_, i) => i + 1)
                          .filter(p => p === 1 || p === totalPages ||
                                       Math.abs(p - page) <= 1)
                          .reduce((acc, p, idx, arr) => {
                            if (idx > 0 && p - arr[idx - 1] > 1) {
                              acc.push('...')
                            }
                            acc.push(p)
                            return acc
                          }, [])
                          .map((p, i) =>
                            p === '...' ? (
                              <span key={`dot-${i}`} className="px-1 text-xs text-muted">…</span>
                            ) : (
                              <button
                                key={p}
                                onClick={() => goTo(p)}
                                className="w-7 h-7 rounded-md text-xs transition-all"
                                style={page === p ? {
                                  background: 'var(--color-accent)',
                                  color: '#fff',
                                } : {
                                  color: 'var(--color-ghost)',
                                }}
                              >
                                {p}
                              </button>
                            )
                          )
                        }

                        {/* Next */}
                        <button
                          onClick={() => goTo(page + 1)}
                          disabled={page === totalPages}
                          className="p-1.5 rounded-md text-ghost hover:text-snow hover:bg-white/5
                                     disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                          title="Next page"
                        >
                          <ChevronRight size={14} />
                        </button>
                        {/* Last */}
                        <button
                          onClick={() => goTo(totalPages)}
                          disabled={page === totalPages}
                          className="p-1.5 rounded-md text-ghost hover:text-snow hover:bg-white/5
                                     disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                          title="Last page"
                        >
                          <ChevronsRight size={14} />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

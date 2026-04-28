import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getStudentHistory,
  deleteAssessment,
  deleteStudentAssessments,
  exportAssessmentPdf,
} from "../api/client";
import Navbar from "../components/Navbar";
import RiskBadge from "../components/RiskBadge";
import ShapChart from "../components/ShapChart";
import InterventionCard from "../components/InterventionCard";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  CalendarDays,
  Activity,
  Trash2,
  FileDown,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
} from "recharts";

// ── PDF download helper ───────────────────────────────────────
async function downloadPdf(assessmentId, studentId) {
  try {
    const res = await exportAssessmentPdf(assessmentId);
    const url = URL.createObjectURL(
      new Blob([res.data], { type: "application/pdf" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `failsafe_${studentId}_${assessmentId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    alert(
      "Could not export PDF. Make sure reportlab is installed on the backend.",
    );
  }
}

const TrendIcon = ({ scores }) => {
  if (scores.length < 2) return <Minus size={14} className="text-muted" />;
  const delta = scores[scores.length - 1] - scores[0];
  if (delta > 5) return <TrendingUp size={14} className="text-red-400" />;
  if (delta < -5)
    return <TrendingDown size={14} className="text-emerald-400" />;
  return <Minus size={14} className="text-muted" />;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-panel border border-border rounded-lg px-3 py-2 text-xs shadow-card">
      <p className="text-muted mb-1">{label}</p>
      <p className="font-mono text-snow">{payload[0].value}% risk</p>
    </div>
  );
};

export default function StudentDetail() {
  const { studentId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selIdx, setSelIdx] = useState(0);

  useEffect(() => {
    getStudentHistory(studentId)
      .then((r) => {
        setData(r.data);
        setSelIdx((r.data.history?.length || 1) - 1);
      })
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [studentId]);

  if (loading)
    return (
      <div className="flex min-h-screen bg-ink">
        <Navbar />
        <main className="ml-56 flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </main>
      </div>
    );

  if (!data || data.count === 0)
    return (
      <div className="flex min-h-screen bg-ink">
        <Navbar />
        <main className="ml-56 flex-1 p-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-sm text-ghost hover:text-snow mb-6"
          >
            <ArrowLeft size={14} /> Back
          </button>
          <div className="card p-8 text-center">
            <p className="text-muted">
              No assessments found for student{" "}
              <span className="font-mono text-ghost">{studentId}</span>
            </p>
          </div>
        </main>
      </div>
    );

  const history = data.history || [];
  const trend = data.trend || [];
  const latest = data.latest || {};
  const selected = history[selIdx];

  const trendChartData = trend.map((t) => ({
    date: new Date(t.date).toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
    }),
    score: t.risk_score,
  }));

  const scores = trend.map((t) => t.risk_score);

  return (
    <div className="flex min-h-screen bg-ink">
      <Navbar />

      <main className="ml-56 flex-1 p-8 max-w-6xl">
        {/* Header */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-sm text-ghost hover:text-snow mb-6 transition-colors"
        >
          <ArrowLeft size={14} /> Back to Dashboard
        </button>

        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="font-display text-2xl text-snow">{studentId}</h1>
            <p className="text-sm text-muted mt-0.5">
              {data.count} assessment{data.count !== 1 ? "s" : ""} on record
            </p>
          </div>
          <div className="flex items-center gap-3">
            <TrendIcon scores={scores} />
            <RiskBadge band={latest.risk_band} score={latest.risk_score} />
            {/* Delete all assessments for this student */}
            <button
              onClick={async () => {
                if (
                  !window.confirm(
                    `Delete ALL assessments for ${studentId}? This cannot be undone.`,
                  )
                )
                  return;
                try {
                  await deleteStudentAssessments(studentId);
                  navigate("/dashboard");
                } catch (err) {
                  console.error("Delete failed:", err);
                }
              }}
              className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg
                         border border-red-500/30 text-red-400 hover:bg-red-500/10
                         transition-all duration-150"
              title="Delete all assessments for this student"
            >
              <Trash2 size={12} />
              Delete All
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          {/* Stats */}
          <div className="card p-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-accent/10 rounded-lg flex items-center justify-center">
              <Activity size={14} className="text-accent" />
            </div>
            <div>
              <p className="text-xs text-muted">Latest Score</p>
              <p className="font-mono text-snow font-medium">
                {latest.risk_score}%
              </p>
            </div>
          </div>
          <div className="card p-4 flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                latest.risk_band === "HIGH"
                  ? "bg-red-500/10"
                  : latest.risk_band === "MEDIUM"
                    ? "bg-amber-500/10"
                    : "bg-emerald-500/10"
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  latest.risk_band === "HIGH"
                    ? "bg-red-500"
                    : latest.risk_band === "MEDIUM"
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                }`}
              />
            </div>
            <div>
              <p className="text-xs text-muted">Risk Band</p>
              <p className="font-mono text-snow font-medium">
                {latest.risk_band}
              </p>
            </div>
          </div>
          <div className="card p-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-panel rounded-lg flex items-center justify-center border border-border">
              <CalendarDays size={14} className="text-ghost" />
            </div>
            <div>
              <p className="text-xs text-muted">Total Assessments</p>
              <p className="font-mono text-snow font-medium">{data.count}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* Left — timeline + trend chart */}
          <div className="col-span-1 space-y-4">
            {/* Risk trend chart */}
            {trendChartData.length > 1 && (
              <div className="card p-4">
                <h2 className="text-xs font-medium text-ghost uppercase tracking-wider mb-3">
                  Risk Trend
                </h2>
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={trendChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2E333D" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: "#6B7280", fontSize: 9 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis domain={[0, 100]} hide />
                    <Tooltip content={<CustomTooltip />} />
                    <ReferenceLine
                      y={65}
                      stroke="#EF4444"
                      strokeDasharray="3 3"
                      strokeOpacity={0.4}
                    />
                    <ReferenceLine
                      y={35}
                      stroke="#F59E0B"
                      strokeDasharray="3 3"
                      strokeOpacity={0.4}
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#6366F1"
                      strokeWidth={2}
                      dot={{ fill: "#6366F1", r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Assessment timeline */}
            <div className="card">
              <div className="px-4 py-3 border-b border-border">
                <h2 className="text-xs font-medium text-ghost uppercase tracking-wider">
                  Assessment History
                </h2>
              </div>
              <div className="divide-y divide-border">
                {history.map((r, i) => (
                  <div
                    key={r.id}
                    className={`flex items-center justify-between px-4 py-3
                                transition-colors group ${
                                  selIdx === i
                                    ? "bg-accent/10 border-l-2 border-l-accent"
                                    : "hover:bg-white/2"
                                }`}
                  >
                    {/* Click left side to select */}
                    <button
                      onClick={() => setSelIdx(i)}
                      className="flex-1 text-left"
                    >
                      <p className="text-xs text-snow font-mono">
                        {r.batch_id}
                      </p>
                      <p className="text-xs text-muted">
                        {new Date(r.created_at).toLocaleDateString()}
                      </p>
                    </button>

                    <div className="flex items-center gap-2">
                      <RiskBadge band={r.risk_band} score={r.risk_score} />
                      {/* Delete this single assessment */}
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          if (!window.confirm("Delete this assessment?"))
                            return;
                          try {
                            await deleteAssessment(r.id);
                            // Remove from local state
                            const newHistory = history.filter(
                              (x) => x.id !== r.id,
                            );
                            setData((d) => ({
                              ...d,
                              history: newHistory,
                              count: d.count - 1,
                            }));
                            // If deleted the selected one, select the previous
                            if (selIdx === i) setSelIdx(Math.max(0, i - 1));
                            // If no assessments left go back
                            if (newHistory.length === 0) navigate("/dashboard");
                          } catch (err) {
                            console.error(err);
                          }
                        }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity
                                   p-1 rounded hover:bg-red-500/10 text-muted hover:text-red-400"
                        title="Delete this assessment"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right — selected assessment detail */}
          <div className="col-span-2 space-y-4">
            {selected ? (
              <>
                {/* SHAP */}
                <div className="card p-5">
                  <h2 className="text-sm font-medium text-ghost mb-3">
                    Key Risk Factors
                    <span className="text-xs text-muted font-normal ml-2">
                      red = increases risk · green = reduces risk
                    </span>
                  </h2>
                  <ShapChart topFactors={selected.top_factors} />
                </div>

                {/* Intervention plan */}
                {selected.intervention_plan && (
                  <div className="card p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h2 className="text-sm font-medium text-ghost">
                        Faculty Action Plan
                      </h2>
                      <button
                        onClick={() => downloadPdf(selected.id, studentId)}
                        className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg
                                   border border-border text-ghost hover:text-snow
                                   hover:border-ghost transition-all duration-150"
                        title="Export this assessment as PDF"
                      >
                        <FileDown size={12} />
                        Export PDF
                      </button>
                    </div>
                    <p className="text-sm text-snow leading-relaxed">
                      {selected.intervention_plan}
                    </p>
                  </div>
                )}

                {/* Intervention cards */}
                {selected.rule_interventions?.length > 0 && (
                  <div className="card p-5">
                    <h2 className="text-sm font-medium text-ghost mb-3">
                      Intervention Actions ({selected.rule_interventions.length}
                      )
                    </h2>
                    <div className="space-y-3">
                      {selected.rule_interventions.map((item, i) => (
                        <InterventionCard key={i} item={item} />
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="card p-8 text-center">
                <p className="text-sm text-muted">
                  Select an assessment from the timeline
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

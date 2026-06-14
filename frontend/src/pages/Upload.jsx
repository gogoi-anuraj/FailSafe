import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import RiskBadge from "../components/RiskBadge";
import InterventionCard from "../components/InterventionCard";
import ShapChart from "../components/ShapChart";
import { predictSingle, predictBatch, getTemplate } from "../api/client";
import {
  Upload as UploadIcon,
  FileText,
  User,
  Download,
  AlertCircle,
  CheckCircle,
  ChevronRight,
} from "lucide-react";

// ── Dropdown options ──────────────────────────────────────────
const STUDY_TIME = [
  { v: 1, l: "Less than 2 hours" },
  { v: 2, l: "2–5 hours" },
  { v: 3, l: "5–10 hours" },
  { v: 4, l: "More than 10 hours" },
];
const TRAVEL_TIME = [
  { v: 1, l: "Less than 15 min" },
  { v: 2, l: "15–30 min" },
  { v: 3, l: "30 min–1 hour" },
  { v: 4, l: "More than 1 hour" },
];
const FAILURES_OPT = [
  { v: 0, l: "None" },
  { v: 1, l: "1 failure" },
  { v: 2, l: "2 failures" },
  { v: 3, l: "3 or more" },
];
const SCALE_1_5 = (labels) => labels.map((l, i) => ({ v: i + 1, l }));
const FAMREL = SCALE_1_5(["Very poor", "Poor", "Average", "Good", "Excellent"]);
const FREETIME = SCALE_1_5([
  "Very little",
  "Little",
  "Moderate",
  "A lot",
  "Very much",
]);
const GOOUT = SCALE_1_5([
  "Very rarely",
  "Rarely",
  "Sometimes",
  "Often",
  "Very often",
]);
const ALC = SCALE_1_5(["Never", "Rarely", "Sometimes", "Often", "Very often"]);
const HEALTH = SCALE_1_5(["Very poor", "Poor", "Fair", "Good", "Very good"]);
const PARENT_EDU = [
  { v: 0, l: "No education" },
  { v: 1, l: "Primary (4th grade)" },
  { v: 2, l: "Middle school" },
  { v: 3, l: "Secondary school" },
  { v: 4, l: "Higher education" },
];

const DEFAULT_FORM = {
  student_id: "",
  G1: "",
  G2: "",
  absences: "",
  failures: 0,
  studytime: 2,
  traveltime: 1,
  famrel: 3,
  freetime: 3,
  goout: 3,
  Dalc: 1,
  Walc: 1,
  health: 3,
  Medu: 2,
  Fedu: 2,
  schoolsup: 0,
  famsup: 1,
  paid: 0,
  activities: 0,
  higher: 1,
  internet: 1,
  romantic: 0,
};

const Select = ({ label, name, options, value, onChange }) => (
  <div>
    <label className="label">{label}</label>
    <select name={name} value={value} onChange={onChange} className="input">
      {options.map((o) => (
        <option key={o.v} value={o.v}>
          {o.l}
        </option>
      ))}
    </select>
  </div>
);

const Toggle = ({ label, name, value, onChange }) => (
  <div className="flex items-center justify-between py-1">
    <span className="text-sm text-ghost">{label}</span>
    <div className="flex gap-2">
      {[
        { v: 1, l: "Yes" },
        { v: 0, l: "No" },
      ].map((opt) => {
        const isActive = value === opt.v;
        return (
          <button
            key={opt.v}
            type="button"
            onClick={() => onChange({ target: { name, value: opt.v } })}
            style={
              isActive
                ? {
                    backgroundColor: "var(--color-accent)",
                    borderColor: "var(--color-accent)",
                    color: "#fff",
                  }
                : {
                    backgroundColor: "transparent",
                    borderColor: "var(--color-border)",
                    color: "var(--color-ghost)",
                  }
            }
            className="text-xs px-3 py-1 rounded-md border transition-all hover:opacity-90"
          >
            {opt.l}
          </button>
        );
      })}
    </div>
  </div>
);

export default function Upload() {
  const navigate = useNavigate();
  const fileRef = useRef();
  const [tab, setTab] = useState("single"); // 'single' | 'batch'
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [batchRes, setBatchRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({
      ...f,
      [name]: isNaN(value) || value === "" ? value : +value,
    }));
  };

  // ── Single student submit ─────────────────────────────────
  const handleSingle = async (e) => {
    e.preventDefault();
    if (!form.student_id.trim()) {
      setError("Student ID is required.");
      return;
    }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const res = await predictSingle({
        ...form,
        G1: +form.G1,
        G2: +form.G2,
        absences: +form.absences,
      });
      setResult(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : detail || "Assessment failed.",
      );
    } finally {
      setLoading(false);
    }
  };

  // ── Batch submit ──────────────────────────────────────────
  const handleBatch = async (file) => {
    if (!file) return;
    setError("");
    setLoading(true);
    setBatchRes(null);
    try {
      const res = await predictBatch(file);
      setBatchRes(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Batch upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file?.name.endsWith(".csv")) handleBatch(file);
    else setError("Please upload a .csv file.");
  };

  // ── Download template ─────────────────────────────────────
  const downloadTemplate = async () => {
    try {
      const res = await getTemplate();
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = "failsafe_template.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Could not download template.");
    }
  };

  return (
    <div className="flex min-h-screen bg-ink">
      <Navbar />

      <main className="ml-56 flex-1 p-8 max-w-5xl">
        <div className="mb-8">
          <h1 className="font-display text-2xl text-snow">New Assessment</h1>
          <p className="text-sm text-muted mt-0.5">
            Assess individual students or upload a class CSV
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate rounded-lg p-1 w-fit mb-6 border border-border">
          {[
            ["single", "Single Student"],
            ["batch", "Batch CSV"],
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={() => {
                setTab(key);
                setError("");
                setResult(null);
                setBatchRes(null);
              }}
              className={`px-4 py-1.5 rounded-md text-sm transition-all border ${
                tab === key
                  ? "bg-accent text-white border-accent shadow-md scale-105"
                  : "text-ghost border-transparent hover:text-snow hover:bg-white/5"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {error && (
          <div
            className="flex items-center gap-2 bg-red-500/10 border border-red-500/30
                          text-red-400 text-sm rounded-lg px-4 py-3 mb-5"
          >
            <AlertCircle size={14} className="shrink-0" />
            {error}
          </div>
        )}

        {/* ── SINGLE STUDENT FORM ───────────────────────────── */}
        {tab === "single" && (
          <div className="grid grid-cols-2 gap-6">
            <form onSubmit={handleSingle} className="space-y-6">
              {/* Student ID */}
              <div className="card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <User size={14} className="text-accent" />
                  <h2 className="text-sm font-medium text-ghost">Student</h2>
                </div>
                <div>
                  <label className="label">Student ID</label>
                  <input
                    name="student_id"
                    value={form.student_id}
                    onChange={handleChange}
                    className="input"
                    placeholder="e.g. STU-001"
                    required
                  />
                </div>
              </div>

              {/* Academic */}
              <div className="card p-5 space-y-4">
                <h2 className="text-sm font-medium text-ghost">Academic</h2>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label">First Period Grade (0–20)</label>
                    <input
                      type="number"
                      name="G1"
                      min={0}
                      max={20}
                      value={form.G1}
                      onChange={handleChange}
                      className="input"
                      placeholder="0–20"
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Second Period Grade (0–20)</label>
                    <input
                      type="number"
                      name="G2"
                      min={0}
                      max={20}
                      value={form.G2}
                      onChange={handleChange}
                      className="input"
                      placeholder="0–20"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="label">Number of Absences</label>
                  <input
                    type="number"
                    name="absences"
                    min={0}
                    max={93}
                    value={form.absences}
                    onChange={handleChange}
                    className="input"
                    placeholder="0–93"
                    required
                  />
                </div>
                <Select
                  label="Past Failures"
                  name="failures"
                  options={FAILURES_OPT}
                  value={form.failures}
                  onChange={handleChange}
                />
                <Select
                  label="Weekly Study Time"
                  name="studytime"
                  options={STUDY_TIME}
                  value={form.studytime}
                  onChange={handleChange}
                />
                <Select
                  label="Travel Time to School"
                  name="traveltime"
                  options={TRAVEL_TIME}
                  value={form.traveltime}
                  onChange={handleChange}
                />
              </div>

              {/* Behaviour */}
              <div className="card p-5 space-y-4">
                <h2 className="text-sm font-medium text-ghost">Behaviour</h2>
                <Select
                  label="Weekday Alcohol Consumption"
                  name="Dalc"
                  options={ALC}
                  value={form.Dalc}
                  onChange={handleChange}
                />
                <Select
                  label="Weekend Alcohol Consumption"
                  name="Walc"
                  options={ALC}
                  value={form.Walc}
                  onChange={handleChange}
                />
                <Select
                  label="Goes Out with Friends"
                  name="goout"
                  options={GOOUT}
                  value={form.goout}
                  onChange={handleChange}
                />
                <Select
                  label="Free Time After School"
                  name="freetime"
                  options={FREETIME}
                  value={form.freetime}
                  onChange={handleChange}
                />
                <Select
                  label="Current Health Status"
                  name="health"
                  options={HEALTH}
                  value={form.health}
                  onChange={handleChange}
                />
              </div>

              {/* Support */}
              <div className="card p-5 space-y-3">
                <h2 className="text-sm font-medium text-ghost mb-1">
                  Support & Home
                </h2>
                <Toggle
                  label="Receiving school support?"
                  name="schoolsup"
                  value={form.schoolsup}
                  onChange={handleChange}
                />
                <Toggle
                  label="Family provides study support?"
                  name="famsup"
                  value={form.famsup}
                  onChange={handleChange}
                />
                <Toggle
                  label="Has internet at home?"
                  name="internet"
                  value={form.internet}
                  onChange={handleChange}
                />
                <Toggle
                  label="Wants higher education?"
                  name="higher"
                  value={form.higher}
                  onChange={handleChange}
                />
                <Toggle
                  label="Attending extra paid classes?"
                  name="paid"
                  value={form.paid}
                  onChange={handleChange}
                />
                <Toggle
                  label="In extracurricular activities?"
                  name="activities"
                  value={form.activities}
                  onChange={handleChange}
                />
                <Toggle
                  label="In a romantic relationship?"
                  name="romantic"
                  value={form.romantic}
                  onChange={handleChange}
                />
              </div>

              {/* Background */}
              <div className="card p-5 space-y-4">
                <h2 className="text-sm font-medium text-ghost">Background</h2>
                <Select
                  label="Mother's Education Level"
                  name="Medu"
                  options={PARENT_EDU}
                  value={form.Medu}
                  onChange={handleChange}
                />
                <Select
                  label="Father's Education Level"
                  name="Fedu"
                  options={PARENT_EDU}
                  value={form.Fedu}
                  onChange={handleChange}
                />
                <Select
                  label="Family Relationship Quality"
                  name="famrel"
                  options={FAMREL}
                  value={form.famrel}
                  onChange={handleChange}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />{" "}
                    Assessing...
                  </>
                ) : (
                  "Assess Student"
                )}
              </button>
            </form>

            {/* Result panel */}
            <div className="space-y-4">
              {result ? (
                <>
                  {/* Risk score card */}
                  <div className="card p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-sm font-medium text-ghost">
                        Assessment Result
                      </h2>
                      <RiskBadge
                        band={result.risk_band}
                        score={result.risk_score}
                      />
                    </div>
                    <div className="flex items-end gap-2 mb-1">
                      <span className="font-display text-5xl text-snow">
                        {result.risk_score}
                      </span>
                      <span className="text-lg text-muted mb-1">%</span>
                    </div>
                    <p className="text-xs text-muted">
                      {result.prediction === "AT-RISK"
                        ? "This student is flagged as at-risk of failure."
                        : "This student is currently on track."}
                    </p>
                    {/* Risk bar */}
                    <div className="mt-4 h-1.5 bg-border rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          result.risk_band === "HIGH"
                            ? "bg-red-500"
                            : result.risk_band === "MEDIUM"
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                        }`}
                        style={{ width: `${result.risk_score}%` }}
                      />
                    </div>
                  </div>

                  {/* SHAP chart */}
                  <div className="card p-5">
                    <h2 className="text-sm font-medium text-ghost mb-3">
                      Key Risk Factors
                      <span className="text-xs text-muted font-normal ml-2">
                        (red = increases risk, green = reduces)
                      </span>
                    </h2>
                    <ShapChart topFactors={result.top_factors} />
                  </div>

                  {/* Intervention plan */}
                  {result.intervention_plan && (
                    <div className="card p-5">
                      <h2 className="text-sm font-medium text-ghost mb-3">
                        Faculty Action Plan
                      </h2>
                      <p className="text-sm text-snow leading-relaxed">
                        {result.intervention_plan}
                      </p>
                      {result.plan_source === "rules" && (
                        <p className="text-xs text-muted mt-2 font-mono">
                          source: rule-based
                        </p>
                      )}
                    </div>
                  )}

                  {/* Intervention cards */}
                  {result.rule_interventions?.length > 0 && (
                    <div className="card p-5">
                      <h2 className="text-sm font-medium text-ghost mb-3">
                        Intervention Actions ({result.rule_interventions.length}
                        )
                      </h2>
                      <div className="space-y-3">
                        {result.rule_interventions.map((item, i) => (
                          <InterventionCard key={i} item={item} />
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="card p-8 flex flex-col items-center justify-center text-center h-64">
                  <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center mb-3">
                    <User size={18} className="text-accent" />
                  </div>
                  <p className="text-sm text-ghost">
                    Fill in the form and click
                  </p>
                  <p className="text-sm text-ghost font-medium">
                    Assess Student
                  </p>
                  <p className="text-xs text-muted mt-2">Results appear here</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── BATCH CSV ─────────────────────────────────────── */}
        {tab === "batch" && (
          <div className="space-y-5 max-w-2xl">
            {/* Download template */}
            <div className="card p-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-snow">
                  Download CSV Template
                </p>
                <p className="text-xs text-muted mt-0.5">
                  Fill this in Excel or Google Sheets, then upload below.
                  Delete the range guide row before uploading.
                </p>
              </div>
              <button
                onClick={downloadTemplate}
                className="btn-ghost flex items-center gap-2 text-sm"
              >
                <Download size={14} />
                Template
              </button>
            </div>

            {/* Drop zone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`card p-12 flex flex-col items-center justify-center cursor-pointer
                          border-2 border-dashed transition-all duration-150 ${
                            dragOver
                              ? "border-accent bg-accent/5"
                              : "border-border hover:border-ghost hover:bg-white/2"
                          }`}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => handleBatch(e.target.files[0])}
              />
              <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center mb-3">
                <UploadIcon size={18} className="text-accent" />
              </div>
              <p className="text-sm font-medium text-snow">
                Drop your CSV here
              </p>
              <p className="text-xs text-muted mt-1">or click to browse</p>
              {loading && (
                <div className="flex items-center gap-2 mt-4 text-sm text-ghost">
                  <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                  Processing students...
                </div>
              )}
            </div>

            {/* Batch results */}
            {batchRes && (
              <div className="card">
                <div className="p-5 border-b border-border">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle size={14} className="text-emerald-400" />
                    <h2 className="text-sm font-medium text-snow">
                      Batch Complete — {batchRes.total_students} students
                      assessed
                    </h2>
                  </div>
                  <div className="flex gap-4 text-xs text-muted mt-2">
                    <span className="text-red-400">
                      {batchRes.high_risk} High Risk
                    </span>
                    <span className="text-amber-400">
                      {batchRes.medium_risk} Medium
                    </span>
                    <span className="text-emerald-400">
                      {batchRes.low_risk} Low
                    </span>
                    {batchRes.skipped_rows > 0 && (
                      <span className="text-muted">
                        {batchRes.skipped_rows} rows skipped
                      </span>
                    )}
                  </div>
                </div>
                <div className="divide-y divide-border max-h-96 overflow-y-auto">
                  {batchRes.students.map((s) => (
                    <div
                      key={s.student_id}
                      onClick={() => navigate(`/student/${s.student_id}`)}
                      className="flex items-center justify-between px-5 py-3
                                    hover:bg-white/2 cursor-pointer transition-colors"
                    >
                      <div>
                        <p className="text-sm font-medium text-snow">
                          {s.student_id}
                        </p>
                        <p className="text-xs text-muted">{s.top_category}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <RiskBadge band={s.risk_band} score={s.risk_score} />
                        <ChevronRight size={14} className="text-muted" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

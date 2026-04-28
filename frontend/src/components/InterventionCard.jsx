const PRIORITY_CONFIG = {
  1: { label: 'Urgent',   color: 'border-l-red-500   bg-red-500/5',   dot: 'bg-red-500'   },
  2: { label: 'Moderate', color: 'border-l-amber-500 bg-amber-500/5', dot: 'bg-amber-500' },
  3: { label: 'Advisory', color: 'border-l-blue-500  bg-blue-500/5',  dot: 'bg-blue-500'  },
}

export default function InterventionCard({ item }) {
  const cfg = PRIORITY_CONFIG[item.priority] || PRIORITY_CONFIG[3]

  return (
    <div className={`border border-border border-l-4 rounded-lg p-4 ${cfg.color}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
          <span className="text-xs font-mono font-medium text-ghost uppercase tracking-wider">
            {cfg.label}
          </span>
          <span className="text-xs text-muted">·</span>
          <span className="text-xs text-ghost">{item.category}</span>
        </div>
        <span className="text-xs font-mono text-muted">
          {item.feature} = {item.value}
        </span>
      </div>
      <p className="text-sm text-snow leading-relaxed">{item.intervention}</p>
    </div>
  )
}

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine
} from 'recharts'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div className="bg-panel border border-border rounded-lg px-3 py-2 text-xs shadow-card">
      <p className="font-mono text-snow">{d.payload.feature}</p>
      <p className={d.value >= 0 ? 'text-red-400' : 'text-emerald-400'}>
        SHAP: {d.value > 0 ? '+' : ''}{d.value.toFixed(4)}
      </p>
    </div>
  )
}

export default function ShapChart({ topFactors }) {
  if (!topFactors?.length) return null

  const data = [...topFactors]
    .map(([feature, value]) => ({ feature, value: +value.toFixed(4) }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 8)

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 16, right: 24, top: 4, bottom: 4 }}
        >
          <XAxis
            type="number"
            tick={{ fill: '#6B7280', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="feature"
            width={72}
            tick={{ fill: '#9CA3AF', fontSize: 11, fontFamily: 'JetBrains Mono' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <ReferenceLine x={0} stroke="#2E333D" strokeWidth={1} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={18}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.value >= 0 ? '#EF4444' : '#10B981'}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

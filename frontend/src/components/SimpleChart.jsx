export function BarChart({ data, color = 'var(--accent)' }) {
  const max = Math.max(...data.map((d) => d.value), 1)
  return (
    <div className="bar-chart">
      {data.map((d) => (
        <div key={d.label} className="bar-col">
          <div
            className="bar-fill"
            style={{ height: `${(d.value / max) * 100}%`, background: color }}
            title={`${d.label}: ${d.value}`}
          />
          <span className="bar-label">{d.label}</span>
          <span className="bar-val">{d.value}</span>
        </div>
      ))}
    </div>
  )
}

export function DonutChart({ data }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1
  const colors = ['#3d9cf5', '#34c77b', '#e8b84a', '#e85d5d', '#9b7bff', '#5eead4']
  let acc = 0
  const stops = data.map((d, i) => {
    const pct = (d.value / total) * 100
    const start = acc
    acc += pct
    return `${colors[i % colors.length]} ${start}% ${acc}%`
  }).join(', ')

  return (
    <div className="donut-wrap">
      <div
        className="donut"
        style={{ background: total ? `conic-gradient(${stops})` : 'var(--border)' }}
      />
      <ul className="donut-legend">
        {data.map((d, i) => (
          <li key={d.label}>
            <span className="dot" style={{ background: colors[i % colors.length] }} />
            {d.label} — {d.value}
          </li>
        ))}
      </ul>
    </div>
  )
}

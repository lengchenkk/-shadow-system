import React from 'react'

export default function History({ state }) {
  const days = []
  for (let i = 13; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    days.push({ key, label: `${d.getMonth() + 1}/${d.getDate()}`, pts: state.logs.filter((l) => l.date === key).reduce((a, l) => a + l.points, 0) })
  }
  const max = Math.max(50, ...days.map((d) => d.pts))
  const totalMin = state.logs.reduce((a, l) => a + l.minutes, 0)
  return (
    <section>
      <div className="section-head"><span className="sys-title">修炼记录</span>
        <span className="sub">累计 {Math.round(totalMin / 6) / 10} 小时</span></div>
      <div className="sys-panel pad chart">
        {days.map((d) => (
          <div key={d.key} className="bar-col" title={`${d.key}：${d.pts} 积分`}>
            <div className="bar-val">{d.pts || ''}</div>
            <div className="bar" style={{ height: `${(d.pts / max) * 140}px` }} />
            <div className="bar-label">{d.label}</div>
          </div>
        ))}
      </div>
      <div className="log-list">
        {state.logs.length === 0 && <div className="sys-panel pad sub">还没有修炼记录。</div>}
        {state.logs.map((l) => (
          <div key={l.id} className="sys-panel pad log">
            <div className="st-row"><b>{l.date}</b><span>{l.minutes} 分钟</span><span className="glow">+{l.points}</span></div>
            {l.summary && <div>{l.summary}</div>}
            {l.comment && <div className="sub">{l.comment}</div>}
          </div>
        ))}
      </div>
    </section>
  )
}

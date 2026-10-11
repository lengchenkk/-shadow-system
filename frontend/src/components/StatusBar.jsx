import React, { useState } from 'react'

export default function StatusBar({ state, muted, onMute, onRename }) {
  const p = state.player
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(p.name)
  const span = Math.max(1, p.xp_next - p.xp_cur)
  const pct = Math.min(100, ((p.xp - p.xp_cur) / span) * 100)

  return (
    <header className="statusbar sys-panel">
      <div className="sb-left">
        <div className="sb-level"><span className="lv">LV.</span>{p.level}</div>
        <div>
          <div className="sb-name">
            {editing ? (
              <input autoFocus value={name} onChange={(e) => setName(e.target.value)}
                onBlur={() => { setEditing(false); onRename(name) }}
                onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()} />
            ) : (
              <span onClick={() => setEditing(true)} title="点击改名">{p.name}</span>
            )}
            {p.title && <span className="equipped">「{p.title}」</span>}
          </div>
          <div className="sb-rank">{p.rank_title}</div>
          <div className="xpbar"><div style={{ width: `${pct}%` }} /></div>
          <div className="xptext">EXP {p.xp} / {p.xp_next}</div>
        </div>
      </div>
      <div className="sb-stats">
        <div><b className="glow">{p.points}</b><span>积分</span></div>
        <div><b>{p.streak}</b><span>连续天数</span></div>
        <div><b>{state.today_base}/{state.daily_cap}</b><span>今日基础分</span></div>
      </div>
      <div className="sb-right">
        {p.penalty_pending ? <div className="penalty-tag">惩罚区域中</div> : null}
        <div className="buffs">
          {state.buff_labels.length ? state.buff_labels.map((b) => <span key={b} className="buff">{b}</span>)
            : <span className="sub">暂无加成</span>}
        </div>
        <button className="icon-btn" onClick={onMute} title="音效">{muted ? '🔇' : '🔊'}</button>
      </div>
    </header>
  )
}

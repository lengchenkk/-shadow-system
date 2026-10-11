import React from 'react'
import { api } from '../api'

export default function Achievements({ state, run }) {
  const eq = state.player.title
  const got = state.achievements.filter((a) => a.unlocked_at).length
  return (
    <section>
      <div className="section-head"><span className="sys-title">成就称号</span><span className="sub">{got} / {state.achievements.length}</span></div>
      <div className="grid ach">
        {state.achievements.map((a) => (
          <div key={a.id} className={a.unlocked_at ? 'sys-panel ach-item on' : 'sys-panel ach-item'}>
            <div className="ach-name">「{a.name}」</div>
            <div className="sub">{a.desc}</div>
            {a.unlocked_at ? (
              <button className="btn small ghost" onClick={() => run(() => api.player({ title: eq === a.name ? '' : a.name }))}>
                {eq === a.name ? '卸下' : '装备称号'}
              </button>
            ) : <div className="sub">未解锁</div>}
          </div>
        ))}
      </div>
    </section>
  )
}

import React from 'react'
import { api } from '../api'
import Silhouette from './Silhouette'

export default function Shop({ state, run }) {
  const pts = state.player.points
  return (
    <section>
      <div className="section-head"><span className="sys-title">影子商店</span><span className="sub">当前积分 {pts}</span></div>
      <div className="grid">
        {state.shop.map((s) => {
          const count = state.army[s.id] || 0
          const owned = count > 0
          const blocked = (!s.repeat && owned) || pts < s.cost
          return (
            <div key={s.id} className={owned ? 'shadow-card sys-panel owned' : 'shadow-card sys-panel'}>
              <Silhouette id={s.id} rank={s.rank} owned={owned} />
              <div className="sc-name">{s.name}{s.repeat && count > 0 && <span className="count">×{count}</span>}</div>
              <div className="sc-rank">{s.rank}</div>
              <div className="sub">{s.desc}</div>
              <div className="buff">{s.buff}</div>
              <div className="sc-cost">{s.cost} 积分</div>
              <button className="btn arise" disabled={blocked} onClick={() => run(() => api.arise(s.id))}>
                {!s.repeat && owned ? '已拥有' : pts < s.cost ? `还差 ${s.cost - pts}` : '起来吧！(ARISE)'}
              </button>
            </div>
          )
        })}
      </div>
    </section>
  )
}

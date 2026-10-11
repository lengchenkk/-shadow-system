import React from 'react'
import Silhouette from './Silhouette'

export default function Army({ state }) {
  const owned = state.shop.filter((s) => state.army[s.id])
  return (
    <section>
      <div className="section-head"><span className="sys-title">影子军团</span><span className="glow">军团战力 {state.army_power}</span></div>
      {owned.length === 0 && <div className="sys-panel sub center pad">军团空无一人。去商店唤醒你的第一个影子吧。</div>}
      <div className="grid">
        {owned.map((s) => (
          <div key={s.id} className="shadow-card sys-panel owned">
            <Silhouette id={s.id} rank={s.rank} owned />
            <div className="sc-name">{s.name}{s.repeat && <span className="count">×{state.army[s.id]}</span>}</div>
            <div className="sc-rank">{s.rank}</div>
            <div className="buff">被动：{s.buff}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

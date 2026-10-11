import React, { useState } from 'react'
import { api } from '../api'

const DESC = { str: '时长分', agi: '每日任务奖励', int: '难题奖励', vit: '坚持奖励', sen: '副本奖励' }
const TIER = { 普通: 'tier-n', 稀有: 'tier-r', 传说: 'tier-l' }

export default function StatusTab({ state, run }) {
  const p = state.player
  const [alloc, setAlloc] = useState({})
  const used = Object.values(alloc).reduce((a, b) => a + b, 0)
  const left = p.attr_points - used
  const add = (k, d) => {
    const v = (alloc[k] || 0) + d
    if (v < 0 || (d > 0 && left <= 0) || p.attrs[k] + v > 50) return
    setAlloc({ ...alloc, [k]: v })
  }
  const confirmAlloc = async () => {
    if (!used || !confirm(`确认分配 ${used} 点属性？`)) return
    await run(() => api.attrs(alloc))
    setAlloc({})
  }
  return (
    <section className="status-tab">
      <div className="sys-panel pad status-window">
        <div className="sys-title center">STATUS</div>
        <div className="st-row"><span>名字：{p.name}</span><span>等级：{p.level}</span></div>
        <div className="st-row"><span>职业：影子君主候补</span><span>称号：{p.title || p.rank_title}</span></div>
        <hr />
        {Object.entries(state.attr_names).map(([k, n]) => (
          <div key={k} className="attr">
            <span className="attr-name">{n}</span>
            <span className="attr-val">{p.attrs[k] + (alloc[k] || 0)}</span>
            <span className="sub">{DESC[k]} +{p.attrs[k] + (alloc[k] || 0)}%</span>
            <button className="icon-btn" onClick={() => add(k, -1)}>－</button>
            <button className="icon-btn" onClick={() => add(k, 1)}>＋</button>
          </div>
        ))}
        <div className="st-row"><span>剩余属性点：<b className="glow">{left}</b></span>
          <button className="btn main small" disabled={!used} onClick={confirmAlloc}>确认分配</button></div>
        <div className="sub">每项上限 50 点</div>
      </div>

      <div className="sys-panel pad">
        <div className="sys-title">宝箱背包</div>
        {state.chests.length === 0 && <div className="sub">暂无宝箱。完成每日任务、击败 Boss、连续 7 天修炼可获得。</div>}
        <div className="chests">
          {state.chests.map((c) => (
            <div key={c.id} className={`chest ${TIER[c.tier]}`}>
              <div className="chest-box" />
              <div>{c.tier}宝箱</div>
              <div className="sub">{c.source}</div>
              <button className="btn small main" onClick={() => run(() => api.openChest(c.id))}>开启</button>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

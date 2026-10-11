import React, { useEffect } from 'react'
import { play } from '../sound'
import Silhouette from './Silhouette'

const DURATION = { arise: 3200, penalty: 3600, levelup: 2600, chest_open: 2600, gate_clear: 3000, achievement: 2200, quest_complete: 2200, chest_get: 1800 }
const SOUND = { arise: 'arise', penalty: 'warning', levelup: 'levelup', chest_open: 'chest', gate_clear: 'levelup', achievement: 'ping', quest_complete: 'levelup', chest_get: 'chest' }

function contentText(c) {
  if (!c) return ''
  if (c.kind === 'points') return `+${c.amount} 积分`
  if (c.kind === 'attr') return `+${c.amount} 属性点`
  return '增益：明日积分 x1.5'
}

export default function Overlays({ queue, onDone }) {
  const e = queue[0]
  useEffect(() => {
    if (!e) return
    play(SOUND[e.type])
    const t = setTimeout(onDone, DURATION[e.type] || 2000)
    return () => clearTimeout(t)
  }, [e, onDone])
  if (!e) return null

  if (e.type === 'arise') {
    return (
      <div className="ov arise-ov" onClick={onDone}>
        <div className="smoke" />
        <Silhouette id={e.soldier.id} rank={e.soldier.rank} owned size={180} />
        <div className="arise-word">ARISE</div>
        <div className="arise-name">起来吧，{e.soldier.name}</div>
      </div>
    )
  }
  if (e.type === 'penalty') {
    return (
      <div className="ov penalty-ov" onClick={onDone}>
        <div className="penalty-box">
          <div className="pen-title">【警告】</div>
          <div>{e.text}</div>
          <div className="sub">{e.task}</div>
        </div>
      </div>
    )
  }
  if (e.type === 'chest_open' || e.type === 'chest_get') {
    const tier = { 普通: 'tier-n', 稀有: 'tier-r', 传说: 'tier-l' }[e.tier]
    return (
      <div className={`ov chest-ov ${tier}`} onClick={onDone}>
        <div className={e.type === 'chest_open' ? 'big-chest opening' : 'big-chest'} />
        <div className="chest-text">{e.type === 'chest_open' ? `${e.tier}宝箱：${contentText(e.content)}` : `获得${e.tier}宝箱！`}</div>
      </div>
    )
  }
  const text = {
    levelup: <>等级提升！<b>LV.{e.level}</b><br />获得 {e.attr_points} 属性点 · {e.title}</>,
    gate_clear: <>副本攻略完成：{e.gate}<br />获得称号「{e.title}」</>,
    achievement: <>获得称号：「{e.name}」</>,
    quest_complete: <>每日任务完成！<br />+{e.points} 积分</>,
  }[e.type]
  return (
    <div className="ov sys-ov" onClick={onDone}>
      <div className="sys-panel modal pop"><div className="sys-title">【系统】</div><div className="glow big">{text}</div></div>
    </div>
  )
}

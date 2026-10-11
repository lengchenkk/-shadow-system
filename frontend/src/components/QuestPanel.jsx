import React from 'react'
import { api } from '../api'

export default function QuestPanel({ state, run }) {
  const q = state.quest
  return (
    <aside className="quest sys-panel">
      <div className="sys-title">【每日任务】</div>
      <div className="sub">准备成为强者</div>
      {!q && <div className="sub">今日任务尚未发布</div>}
      {q && q.objectives.map((o, i) => {
        const done = o.progress >= o.target
        return (
          <div key={i} className={done ? 'qitem done' : 'qitem'}>
            <span className="box">{done ? '✔' : ''}</span>
            <div className="qtext">
              <div>{o.text}</div>
              {o.kind !== 'other' && <div className="sub">[{Math.min(o.progress, o.target)}/{o.target}]{o.kind === 'minutes' ? ' 分钟' : ' 道'}</div>}
            </div>
            {o.kind === 'other' && !done && !q.completed && (
              <button className="btn ghost small" onClick={() => run(() => api.questDone(i))}>完成</button>
            )}
          </div>
        )
      })}
      {q?.completed && <div className="glow">任务完成，奖励已发放</div>}
      <div className="warn-note">⚠ 未完成每日任务，将被传送至惩罚区域。</div>
      {state.player.penalty_pending ? <div className="penalty-tag">惩罚任务：今天额外学习 30 分钟</div> : null}
    </aside>
  )
}

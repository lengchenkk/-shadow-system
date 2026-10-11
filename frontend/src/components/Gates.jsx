import React, { useState } from 'react'
import { api } from '../api'

const RANKS = ['E', 'D', 'C', 'B', 'A', 'S']

export default function Gates({ state, run }) {
  const [form, setForm] = useState({ name: '', rank: 'C', exam_date: '', stages: '' })
  const create = () => {
    if (!form.name.trim()) return
    run(() => api.newGate({ ...form, stages: form.stages.split('\n').map((s) => s.trim()).filter(Boolean) }))
    setForm({ name: '', rank: 'C', exam_date: '', stages: '' })
  }
  return (
    <section>
      <div className="section-head"><span className="sys-title">传送门副本</span>
        <span className="sub">也可以在对话里说"把高数期末建成副本"</span></div>
      <div className="sys-panel pad gate-form">
        <input placeholder="副本名（课程或考试）" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <select value={form.rank} onChange={(e) => setForm({ ...form, rank: e.target.value })}>
          {RANKS.map((r) => <option key={r} value={r}>{r} 级</option>)}
        </select>
        <input type="date" value={form.exam_date} onChange={(e) => setForm({ ...form, exam_date: e.target.value })} />
        <textarea rows={3} placeholder="关卡（每行一个，可留空使用默认 5 层）" value={form.stages}
          onChange={(e) => setForm({ ...form, stages: e.target.value })} />
        <button className="btn main" onClick={create}>开启传送门</button>
      </div>
      <div className="grid gates">
        {state.gates.map((g) => {
          const done = g.stages.filter((s) => s.cleared).length
          return (
            <div key={g.id} className={`sys-panel gate rank-${g.rank} ${g.cleared ? 'cleared' : ''}`}>
              <div className="portal"><span>{g.rank}</span></div>
              <div className="gate-name">{g.name}</div>
              <div className="sub">{g.cleared ? '已攻略' : g.days_left != null ? `距离 Boss 战 ${g.days_left} 天` : '未设定考试日期'}</div>
              <div className="xpbar"><div style={{ width: `${(done / g.stages.length) * 100}%` }} /></div>
              <ol className="stages">
                {g.stages.map((s) => (
                  <li key={s.id} className={s.cleared ? 'cleared' : s.is_boss ? 'boss' : ''}>
                    <span>{s.name}</span>
                    {!s.cleared && (
                      <button className="btn ghost small"
                        onClick={() => confirm(`确认已攻克「${s.name}」？`) && run(() => api.clearStage(g.id, s.idx))}>
                        {s.is_boss ? '挑战' : '通关'}
                      </button>
                    )}
                  </li>
                ))}
              </ol>
              <button className="btn ghost small danger" onClick={() => confirm('删除此副本？') && run(() => api.delGate(g.id))}>删除</button>
            </div>
          )
        })}
      </div>
    </section>
  )
}

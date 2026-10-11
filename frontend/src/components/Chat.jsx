import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { play } from '../sound'
import EventCard from './EventCard'

const CHIPS = ['汇报今天的学习', '我遇到了难题', '我要召唤影子', '查看我的状态']

export default function Chat({ state, refresh, handleEvents, notify }) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [pending, setPending] = useState(null)
  const listRef = useRef(null)
  const msgs = state.messages

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [msgs.length, busy])

  async function send(t) {
    const content = (t ?? text).trim()
    if (!content || busy) return
    setText('')
    setPending(content)
    setBusy(true)
    try {
      const r = await api.chat(content)
      play('ping')
      handleEvents(r.events)
      await refresh()
    } catch (e) {
      notify(`【系统】${e.message}`, true)
      setText(content)
    } finally {
      setPending(null)
      setBusy(false)
    }
  }

  async function clear() {
    if (!confirm('确定清空全部对话？（积分等数据不受影响）')) return
    await api.clearChat()
    refresh()
  }

  return (
    <section className="chat sys-panel">
      <div className="panel-head">
        <span className="sys-title">与系统对话</span>
        <span className="sub">{state.settings.demo || !state.settings.has_key ? '演示模式' : state.settings.model}</span>
        <button className="btn ghost small" onClick={clear}>清空对话</button>
      </div>
      <div className="msgs" ref={listRef}>
        {msgs.length === 0 && <div className="sub center">【系统】随时向我汇报你的修炼。</div>}
        {msgs.map((m) => (
          <div key={m.id} className={`msg ${m.role}`}>
            {m.content && <div className="bubble">{m.content}</div>}
            {m.cards?.map((c, i) => <EventCard key={i} e={c} />)}
          </div>
        ))}
        {pending && <div className="msg user"><div className="bubble">{pending}</div></div>}
        {busy && <div className="msg assistant"><div className="bubble typing">系统正在分析<span>…</span></div></div>}
      </div>
      <div className="chips">
        {CHIPS.map((c) => <button key={c} className="chip" onClick={() => send(c)} disabled={busy}>{c}</button>)}
      </div>
      <div className="composer">
        <textarea rows={2} value={text} placeholder="向系统汇报今天的修炼……（Enter 发送，Shift+Enter 换行）"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }} />
        <button className="btn main" onClick={() => send()} disabled={busy}>发送</button>
      </div>
    </section>
  )
}

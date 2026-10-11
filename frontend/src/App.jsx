import React, { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { play, isMuted, setMuted } from './sound'
import StatusBar from './components/StatusBar'
import Chat from './components/Chat'
import QuestPanel from './components/QuestPanel'
import Gates from './components/Gates'
import Shop from './components/Shop'
import Army from './components/Army'
import StatusTab from './components/StatusTab'
import Achievements from './components/Achievements'
import History from './components/History'
import Settings from './components/Settings'
import Overlays from './components/Overlays'

const TABS = [
  ['chat', '与系统对话'], ['gates', '副本'], ['shop', '影子商店'], ['army', '影子军团'],
  ['status', '状态'], ['ach', '成就'], ['history', '修炼记录'], ['settings', 'AI 设置'],
]

// 哪些事件需要全屏/弹窗演出
const OVERLAY_TYPES = ['arise', 'levelup', 'chest_open', 'penalty', 'gate_clear', 'achievement', 'quest_complete', 'chest_get']

export default function App() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState('chat')
  const [queue, setQueue] = useState([])
  const [toast, setToast] = useState(null)
  const [muted, setMutedState] = useState(isMuted())

  const refresh = useCallback(async () => {
    const s = await api.state()
    setState(s)
    return s
  }, [])

  const handleEvents = useCallback((events = []) => {
    const ov = events.filter((e) => OVERLAY_TYPES.includes(e.type))
    if (events.some((e) => e.type === 'award')) play('coin')
    if (ov.length) setQueue((q) => [...q, ...ov])
  }, [])

  const notify = useCallback((text, bad = false) => {
    setToast({ text, bad })
    setTimeout(() => setToast(null), 2600)
  }, [])

  // 包装：执行一个返回 {events} 的操作，然后刷新
  const run = useCallback(async (fn) => {
    try {
      const r = await fn()
      if (r && r.events) handleEvents(r.events)
      await refresh()
      return r
    } catch (e) {
      notify(`【系统】${e.message}`, true)
      throw e
    }
  }, [handleEvents, refresh, notify])

  useEffect(() => {
    refresh().then((s) => handleEvents(s.events)).catch((e) => notify(`无法连接后端：${e.message}`, true))
  }, [refresh, handleEvents, notify])

  if (!state) {
    return <div className="boot"><div className="sys-panel">【系统】正在连接……</div></div>
  }

  const p = state.player

  return (
    <div className="app">
      <div className="scanlines" />
      <StatusBar state={state} muted={muted}
        onMute={() => { setMuted(!muted); setMutedState(!muted) }}
        onRename={(name) => run(() => api.player({ name }))} />

      <nav className="tabs">
        {TABS.map(([k, label]) => (
          <button key={k} className={tab === k ? 'tab active' : 'tab'} onClick={() => setTab(k)}>
            {label}
            {k === 'status' && (p.attr_points > 0 || state.chests.length > 0) && <span className="dot" />}
          </button>
        ))}
      </nav>

      <main className="main">
        {tab === 'chat' && (
          <div className="chat-layout">
            <Chat state={state} refresh={refresh} handleEvents={handleEvents} notify={notify} />
            <QuestPanel state={state} run={run} />
          </div>
        )}
        {tab === 'gates' && <Gates state={state} run={run} />}
        {tab === 'shop' && <Shop state={state} run={run} />}
        {tab === 'army' && <Army state={state} />}
        {tab === 'status' && <StatusTab state={state} run={run} />}
        {tab === 'ach' && <Achievements state={state} run={run} />}
        {tab === 'history' && <History state={state} />}
        {tab === 'settings' && <Settings state={state} run={run} refresh={refresh} notify={notify} />}
      </main>

      {!p.accepted && (
        <div className="modal-bg">
          <div className="sys-panel modal">
            <div className="sys-title">【系统】</div>
            <p className="glow big">你已被选为玩家。<br />是否接受？</p>
            <p className="sub">汇报每日修炼，获取积分，唤醒属于你的影子军团。</p>
            <button className="btn main" onClick={() => { play('ping'); run(() => api.player({ accepted: true })) }}>接受</button>
          </div>
        </div>
      )}

      <Overlays queue={queue} onDone={() => setQueue((q) => q.slice(1))} />
      {toast && <div className={toast.bad ? 'toast bad' : 'toast'}>{toast.text}</div>}
    </div>
  )
}

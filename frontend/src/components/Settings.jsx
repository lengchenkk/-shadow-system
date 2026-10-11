import React, { useState } from 'react'
import { api } from '../api'

export default function Settings({ state, run, refresh, notify }) {
  const st = state.settings
  const [baseUrl, setBaseUrl] = useState(st.base_url)
  const [key, setKey] = useState('')
  const [show, setShow] = useState(false)
  const [model, setModel] = useState(st.model)
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(false)

  const save = async (extra = {}) => {
    await api.settings({ base_url: baseUrl, api_key: key || undefined, model, ...extra })
    setKey('')
    await refresh()
  }

  const fetchModels = async () => {
    setLoading(true)
    try {
      const r = await api.models({ base_url: baseUrl, api_key: key || undefined })
      setModels(r.models)
      notify(`【系统】已拉取 ${r.models.length} 个模型`)
    } catch (e) {
      notify(`【系统】${e.message}`, true)
    } finally {
      setLoading(false)
    }
  }

  const exportSave = async () => {
    const data = await api.exportSave()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `shadow-save-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
  }

  const importSave = (e) => {
    const f = e.target.files[0]
    if (!f) return
    f.text().then(async (t) => {
      if (!confirm('导入会覆盖当前全部进度，确定？')) return
      await run(() => api.importSave(JSON.parse(t)))
      notify('【系统】存档已导入')
    }).catch(() => notify('【系统】存档文件无效', true))
    e.target.value = ''
  }

  return (
    <section className="settings">
      <div className="sys-panel pad">
        <div className="sys-title">AI 设置</div>
        <label>API Base URL（OpenAI 兼容）
          <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="https://api.openai.com/v1" />
        </label>
        <label>API Key {st.has_key && <span className="sub">（已保存，留空则不修改）</span>}
          <div className="row">
            <input type={show ? 'text' : 'password'} value={key} onChange={(e) => setKey(e.target.value)} placeholder="sk-..." />
            <button className="btn ghost small" onClick={() => setShow(!show)}>{show ? '隐藏' : '显示'}</button>
          </div>
        </label>
        <div className="row">
          <button className="btn ghost" onClick={fetchModels} disabled={loading}>{loading ? '拉取中…' : '拉取模型'}</button>
        </div>
        <label>模型
          <input list="model-list" value={model} onChange={(e) => setModel(e.target.value)} placeholder="选择或手动输入模型名" />
          <datalist id="model-list">{models.map((m) => <option key={m} value={m} />)}</datalist>
        </label>
        <label className="toggle">
          <input type="checkbox" checked={st.demo} onChange={(e) => save({ demo: e.target.checked })} />
          演示模式（不调用 AI，本地规则评分）
        </label>
        <button className="btn main" onClick={() => save().then(() => notify('【系统】设置已保存'))}>保存设置</button>
        <div className="sub">密钥保存在你本机的 SQLite 数据库中，只由后端转发给你填写的接口，不会出现在导出的存档里。</div>
      </div>

      <div className="sys-panel pad">
        <div className="sys-title">存档</div>
        <div className="row">
          <button className="btn ghost" onClick={exportSave}>导出存档</button>
          <label className="btn ghost">导入存档<input type="file" accept=".json" hidden onChange={importSave} /></label>
          <button className="btn ghost" onClick={() => run(() => api.debugPoints())}>+1000 测试积分</button>
        </div>
      </div>
    </section>
  )
}

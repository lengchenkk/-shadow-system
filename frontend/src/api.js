async function req(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
  return data
}

export const api = {
  state: () => req('GET', '/api/state'),
  player: (b) => req('PUT', '/api/player', b),
  settings: (b) => req('PUT', '/api/settings', b),
  models: (b) => req('POST', '/api/models', b),
  chat: (text) => req('POST', '/api/chat', { text }),
  clearChat: () => req('DELETE', '/api/messages'),
  arise: (id) => req('POST', `/api/arise/${id}`),
  attrs: (alloc) => req('POST', '/api/attrs', { alloc }),
  openChest: (id) => req('POST', `/api/chests/${id}/open`),
  newGate: (b) => req('POST', '/api/gates', b),
  clearStage: (g, i) => req('POST', `/api/gates/${g}/stages/${i}/clear`),
  delGate: (g) => req('DELETE', `/api/gates/${g}`),
  questDone: (i) => req('POST', `/api/quest/${i}/done`),
  exportSave: () => req('GET', '/api/export'),
  importSave: (d) => req('POST', '/api/import', d),
  debugPoints: () => req('POST', '/api/debug/points'),
}

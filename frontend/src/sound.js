// Web Audio 合成音效，无需音频文件
let ctx = null
let muted = localStorage.getItem('shadow_muted') === '1'

export const isMuted = () => muted
export function setMuted(v) {
  muted = v
  localStorage.setItem('shadow_muted', v ? '1' : '0')
}

function ac() {
  if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)()
  if (ctx.state === 'suspended') ctx.resume()
  return ctx
}

function tone(freq, start, dur, type = 'sine', gain = 0.15, slideTo) {
  const c = ac()
  const o = c.createOscillator()
  const g = c.createGain()
  o.type = type
  o.frequency.setValueAtTime(freq, c.currentTime + start)
  if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, c.currentTime + start + dur)
  g.gain.setValueAtTime(0.0001, c.currentTime + start)
  g.gain.exponentialRampToValueAtTime(gain, c.currentTime + start + 0.02)
  g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + start + dur)
  o.connect(g).connect(c.destination)
  o.start(c.currentTime + start)
  o.stop(c.currentTime + start + dur + 0.05)
}

export function play(name) {
  if (muted) return
  try {
    switch (name) {
      case 'ping':
        tone(880, 0, 0.12, 'sine', 0.1); tone(1320, 0.08, 0.18, 'sine', 0.08); break
      case 'levelup':
        [523, 659, 784, 1047].forEach((f, i) => tone(f, i * 0.1, 0.35, 'triangle', 0.12)); break
      case 'arise':
        tone(110, 0, 1.4, 'sawtooth', 0.2, 40); tone(55, 0, 1.6, 'sine', 0.3, 30); tone(220, 0.3, 1.0, 'square', 0.04, 80); break
      case 'chest':
        [1200, 1600, 2000, 2400, 3000].forEach((f, i) => tone(f, i * 0.06, 0.25, 'sine', 0.06)); break
      case 'warning':
        for (let i = 0; i < 4; i++) tone(440, i * 0.4, 0.3, 'square', 0.08, 330); break
      case 'coin':
        tone(988, 0, 0.08, 'square', 0.06); tone(1319, 0.08, 0.2, 'square', 0.06); break
      default:
    }
  } catch { /* 浏览器不支持则忽略 */ }
}

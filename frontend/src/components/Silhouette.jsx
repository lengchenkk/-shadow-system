import React from 'react'

// 不同影子用不同的 SVG 剪影，颜色由等级决定
const PATHS = {
  soldier: 'M50 12a10 10 0 1 1 0 20a10 10 0 1 1 0-20M35 36h30l6 30h-8l-3 26h-8l-2-20-2 20h-8l-3-26h-8z',
  knight: 'M50 8l9 8v12a9 9 0 0 1-18 0V16zM32 38h36l8 26-8 2-2 28H58l-3-22-5 0-3 22H38l-2-28-8-2zM76 20l4 0 0 50-4 0z',
  tusk: 'M50 10c12 0 18 10 18 20c0 6-4 10-8 12l14 50H26l14-50c-4-2-8-6-8-12c0-10 6-20 18-20zM30 24l-10-8M70 24l10-8M18 40l8 0 0 45-8 0z',
  iron: 'M50 10a11 11 0 1 1 0 22a11 11 0 1 1 0-22M30 36h40l6 56H24zM12 40h22v36c0 6-11 12-11 12S12 82 12 76z',
  tank: 'M28 22a9 9 0 1 1 10-6M72 22a9 9 0 1 0-10-6M50 14c16 0 26 12 26 28c0 30-10 50-26 50S24 72 24 42c0-16 10-28 26-28z',
  greed: 'M50 9a10 10 0 1 1 0 20a10 10 0 1 1 0-20M34 33h32l10 30-10 4-2 26H36l-2-26-10-4zM74 30l10-14 3 2-10 14z',
  kaisel: 'M50 30c6 0 10 6 10 12l30-18-14 26 12 4-26 10-4 26h-16l-4-26-26-10 12-4L10 24l30 18c0-6 4-12 10-12zM46 18l4-10 4 10z',
  igris: 'M50 6l10 10v14a10 10 0 0 1-20 0V16zM56 8l14-4-8 10zM30 38h40l10 54H20zM78 6l3 0 0 60-3 0zM72 18h15v3H72z',
  beru: 'M50 12c8 0 12 8 12 14l12-12-6 18c4 2 6 6 6 10l14 6-14 2-6 42H32l-6-42-14-2 14-6c0-4 2-8 6-10l-6-18 12 12c0-6 4-14 12-14z',
  bellion: 'M50 4l8 10v12a8 8 0 0 1-16 0V14zM26 32h48l14 62H12zM86 8c4 20 4 50-4 70l-3-1c7-20 7-48 3-68zM14 8c-4 20-4 50 4 70l3-1c-7-20-7-48-3-68z',
}
const COLORS = { 普通级: '#5aa9ff', 精英级: '#7d7dff', 骑士级: '#9b6bff', 精英骑士级: '#b45cff', 骑士团长级: '#ff4d6d', 元帅级: '#c04dff', 大元帅: '#e0b3ff' }

export default function Silhouette({ id, rank, owned, size = 90 }) {
  const color = COLORS[rank] || '#7d7dff'
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} className={owned ? 'sil owned' : 'sil'}
      style={{ '--c': color }}>
      <path d={PATHS[id] || PATHS.soldier} fill={owned ? color : '#0b0f1e'} stroke={color} strokeWidth="1.5" />
      {owned && <><circle cx="45" cy="20" r="1.6" fill="#fff" /><circle cx="55" cy="20" r="1.6" fill="#fff" /></>}
    </svg>
  )
}

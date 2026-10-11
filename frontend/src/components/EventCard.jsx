import React from 'react'

const TIER = { 普通: 'tier-n', 稀有: 'tier-r', 传说: 'tier-l' }

export default function EventCard({ e }) {
  switch (e.type) {
    case 'award':
      return (
        <div className="card award">
          <div className="card-title">【系统】{e.extra ? '追加修炼结算' : '每日任务完成'}</div>
          <div className="card-points">+{e.points} 积分</div>
          <ul className="breakdown">
            {e.breakdown.map((b, i) => (
              <li key={i} className={b.kind === 'bonus' ? 'bonus' : ''}><span>{b.item}</span><span>+{b.points}</span></li>
            ))}
          </ul>
          {e.summary && <div className="sub">修炼内容：{e.summary}</div>}
          {e.title && <div className="title-get">获得称号：「{e.title}」</div>}
          {e.tomorrow_quest && <div className="urgent">明日紧急任务：{e.tomorrow_quest}</div>}
          <div className="sub">连续修炼 {e.streak} 天</div>
        </div>
      )
    case 'arise':
      return <div className="card arise-card">ARISE —— {e.soldier.name} 已加入影子军团{e.soldier.repeat ? `（×${e.count}）` : ''}</div>
    case 'levelup':
      return <div className="card levelup">【系统】等级提升！LV.{e.level}｜获得 {e.attr_points} 属性点｜{e.title}</div>
    case 'quest_complete':
      return <div className="card">【系统】每日任务全部完成 +{e.points} 积分</div>
    case 'chest_get':
      return <div className={`card ${TIER[e.tier]}`}>【系统】获得{e.tier}宝箱（{e.source}），前往「状态」开启</div>
    case 'achievement':
      return <div className="card ach-card">【系统】获得称号：「{e.name}」</div>
    case 'gate_open':
      return <div className={`card gate-card rank-${e.rank}`}>【系统】{e.rank}级传送门已开启：{e.name}</div>
    case 'stage_clear':
      return <div className="card">【系统】{e.boss ? 'Boss 已击败' : '关卡通关'}：{e.stage} +{e.points} 积分</div>
    case 'gate_clear':
      return <div className="card levelup">【系统】副本「{e.gate}」已攻略完成！获得称号「{e.title}」</div>
    case 'shield':
    case 'pardon':
    case 'penalty_clear':
      return <div className="card">【系统】{e.text}</div>
    case 'penalty':
      return <div className="card penalty-card">【警告】{e.text}<br />{e.task}</div>
    case 'quest':
      return null
    default:
      return null
  }
}

"""游戏规则：等级、影子、技能加成、属性、每日任务、副本、宝箱、成就。

所有会改变数据的函数都接收一个 sqlite 连接 c 和一个 events 列表，
events 会返回给前端用于播放动画 / 音效 / 在聊天里显示卡片。
"""
import datetime as dt
import json
import math
import random

DAILY_CAP = 500  # AI 每日基础积分上限

# ---------------------------------------------------------------- 影子
SHADOWS = [
    {"id": "soldier", "name": "普通影子步兵", "rank": "普通级", "cost": 50, "repeat": True, "power": 10,
     "desc": "最基础的影子士兵，数量就是力量。", "buff": "积分 +1%/只（上限 +10%）"},
    {"id": "knight", "name": "影子骑士", "rank": "精英级", "cost": 150, "repeat": True, "power": 40,
     "desc": "身披黑甲的骑士，军团的中坚。", "buff": "积分 +2%/只（上限 +10%）"},
    {"id": "tusk", "name": "尖牙 Tusk", "rank": "精英级", "cost": 800, "repeat": False, "power": 300,
     "desc": "高阶兽人萨满，擅长强大的魔法。", "buff": "难题奖励 +20%"},
    {"id": "iron", "name": "铁 Iron", "rank": "骑士级", "cost": 1000, "repeat": False, "power": 350,
     "desc": "坚不可摧的盾卫，替主人挡下一切。", "buff": "每周一次断签保护"},
    {"id": "tank", "name": "坦克 Tank", "rank": "骑士级", "cost": 1200, "repeat": False, "power": 400,
     "desc": "冰原熊王，皮糙肉厚的冲锋者。", "buff": "时长分 +10%"},
    {"id": "greed", "name": "格利德 Greed", "rank": "精英骑士级", "cost": 1500, "repeat": False, "power": 500,
     "desc": "前猎人转化的影子，战斗经验丰富。", "buff": "每日任务奖励 +20%"},
    {"id": "kaisel", "name": "凯塞尔 Kaisel", "rank": "精英骑士级", "cost": 2500, "repeat": False, "power": 700,
     "desc": "天空飞龙坐骑，载着主人穿越战场。", "buff": "副本奖励 +20%"},
    {"id": "igris", "name": "伊格里斯 Igris", "rank": "骑士团长级", "cost": 4000, "repeat": False, "power": 1200,
     "desc": "血红骑士团长，最忠诚的剑。", "buff": "全部积分 +10%"},
    {"id": "beru", "name": "贝尔 Beru", "rank": "元帅级", "cost": 6000, "repeat": False, "power": 2000,
     "desc": "蚂蚁王，凶猛而狂热的忠臣。", "buff": "每周一次免除惩罚区域"},
    {"id": "bellion", "name": "贝利昂 Bellion", "rank": "大元帅", "cost": 10000, "repeat": False, "power": 4000,
     "desc": "影子军团最强的大元帅。", "buff": "全部积分 +20%，Boss 奖励翻倍"},
]
SHADOW_BY_ID = {s["id"]: s for s in SHADOWS}

TITLES_BY_LEVEL = [(1, "E级猎人"), (5, "D级猎人"), (10, "C级猎人"), (15, "B级猎人"), (20, "A级猎人"),
                   (30, "S级猎人"), (40, "国家级猎人"), (50, "影之君主")]

ATTRS = {"str": "力量", "agi": "敏捷", "int": "智力", "vit": "体力", "sen": "感知"}
ATTR_CAP = 50

GATE_REWARD = {"E": 50, "D": 80, "C": 120, "B": 180, "A": 250, "S": 400}

ACHIEVEMENTS = [
    ("first_award", "初次觉醒", "完成第一次结算"),
    ("streak7", "七日不辍", "连续学习 7 天"),
    ("streak30", "月之修行者", "连续学习 30 天"),
    ("hours10", "十小时修炼", "累计学习 10 小时"),
    ("hours100", "百小时苦修", "累计学习 100 小时"),
    ("first_shadow", "起来吧", "召唤第一只影子"),
    ("igris", "血红骑士之主", "召唤伊格里斯"),
    ("beru", "蚂蚁王之主", "召唤贝尔"),
    ("bellion", "影之君主", "召唤贝利昂"),
    ("first_gate", "副本征服者", "通关第一个副本"),
    ("s_boss", "红色传送门", "击败 S 级 Boss"),
    ("lv10", "C级觉醒", "达到 10 级"),
    ("lv30", "S级觉醒", "达到 30 级"),
    ("legend_chest", "天选之人", "开启传说宝箱"),
    ("quest10", "任务狂人", "完成 10 次每日任务"),
]

QUEST_POOL = [
    {"text": "专注学习 60 分钟", "kind": "minutes", "target": 60},
    {"text": "专注学习 90 分钟", "kind": "minutes", "target": 90},
    {"text": "专注学习 120 分钟", "kind": "minutes", "target": 120},
    {"text": "攻克 1 道难题", "kind": "problems", "target": 1},
    {"text": "攻克 2 道难题", "kind": "problems", "target": 2},
    {"text": "复习昨天学过的内容", "kind": "other", "target": 1},
    {"text": "整理一份学习笔记", "kind": "other", "target": 1},
    {"text": "做一套练习题并订正", "kind": "other", "target": 1},
]


def today():
    return dt.date.today().isoformat()


def week_key(d=None):
    d = d or dt.date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w}"


def level_for_xp(xp):
    return int(math.floor(math.sqrt(max(xp, 0) / 50))) + 1


def xp_for_level(level):
    return 50 * (level - 1) ** 2


def title_for_level(level):
    t = TITLES_BY_LEVEL[0][1]
    for lv, name in TITLES_BY_LEVEL:
        if level >= lv:
            t = name
    return t


def army(c):
    return {r["soldier_id"]: r["count"] for r in c.execute("SELECT * FROM army WHERE count>0")}


def buffs(c, p=None):
    """返回当前生效的各类加成百分比。"""
    from . import db
    p = p or db.player(c)
    a = army(c)
    at = p["attrs"]
    b = {
        "global": min(a.get("soldier", 0) * 1, 10) + min(a.get("knight", 0) * 2, 10)
        + (10 if a.get("igris") else 0) + (20 if a.get("bellion") else 0),
        "time": min(at.get("str", 0), ATTR_CAP) + (10 if a.get("tank") else 0),
        "problem": min(at.get("int", 0), ATTR_CAP) + (20 if a.get("tusk") else 0),
        "streak": min(at.get("vit", 0), ATTR_CAP),
        "quest": min(at.get("agi", 0), ATTR_CAP) + (20 if a.get("greed") else 0),
        "gate": min(at.get("sen", 0), ATTR_CAP) + (20 if a.get("kaisel") else 0),
        "boss_double": bool(a.get("bellion")),
        "iron_shield": bool(a.get("iron")) and p.get("shield_week") != week_key(),
        "beru_pardon": bool(a.get("beru")) and p.get("beru_week") != week_key(),
        "boost_today": p.get("boost_date") == today(),
    }
    return b


def buff_labels(b):
    out = []
    if b["global"]:
        out.append(f"全部积分 +{b['global']}%")
    for k, n in (("time", "时长分"), ("problem", "难题奖励"), ("streak", "坚持奖励"), ("quest", "每日任务奖励"), ("gate", "副本奖励")):
        if b[k]:
            out.append(f"{n} +{b[k]}%")
    if b["boss_double"]:
        out.append("Boss 奖励翻倍")
    if b["iron_shield"]:
        out.append("铁之盾：断签保护可用")
    if b["beru_pardon"]:
        out.append("贝尔：惩罚豁免可用")
    if b["boost_today"]:
        out.append("今日积分 x1.5")
    return out


# ---------------------------------------------------------------- 积分 / 经验
def gain_points(c, amount, events, reason=""):
    """增加积分与经验，处理升级。"""
    from . import db
    if amount <= 0:
        return
    p = db.player(c)
    xp = p["xp"] + amount
    new_level = level_for_xp(xp)
    fields = {"points": p["points"] + amount, "xp": xp}
    if new_level > p["level"]:
        gained = (new_level - p["level"]) * 5
        fields["level"] = new_level
        fields["attr_points"] = p["attr_points"] + gained
        events.append({"type": "levelup", "level": new_level, "attr_points": gained,
                       "title": title_for_level(new_level)})
    db.update_player(c, **fields)
    check_achievements(c, events)


# ---------------------------------------------------------------- 每日刷新
def daily_tick(c, events, ai_quest=None):
    """每天第一次打开时：检查昨日任务 -> 惩罚区域；发布今日任务。"""
    from . import db
    p = db.player(c)
    t = today()
    if p["last_tick_date"] == t:
        return
    y = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    yq = c.execute("SELECT * FROM daily_quests WHERE date=?", (y,)).fetchone()
    if yq and not yq["completed"] and p["accepted"]:
        b = buffs(c, p)
        if b["beru_pardon"]:
            db.update_player(c, beru_week=week_key())
            events.append({"type": "pardon", "text": "贝尔挡在你身前：本次惩罚区域已被豁免。"})
        else:
            db.update_player(c, penalty_pending=1)
            events.append({"type": "penalty", "text": "未完成每日任务，即将传送至惩罚区域。",
                           "task": "惩罚任务：今天额外学习 30 分钟（完成前坚持奖励暂停）"})
    if not c.execute("SELECT 1 FROM daily_quests WHERE date=?", (t,)).fetchone():
        objs = ai_quest or random_quest()
        set_quest(c, t, objs)
        events.append({"type": "quest", "objectives": objs})
    db.update_player(c, last_tick_date=t)


def random_quest():
    mins = random.choice([q for q in QUEST_POOL if q["kind"] == "minutes"])
    prob = random.choice([q for q in QUEST_POOL if q["kind"] == "problems"])
    other = random.choice([q for q in QUEST_POOL if q["kind"] == "other"])
    return [dict(mins, progress=0), dict(prob, progress=0), dict(other, progress=0)]


def set_quest(c, date, objectives):
    clean = []
    for o in objectives[:4]:
        kind = o.get("kind") if o.get("kind") in ("minutes", "problems", "other") else "other"
        clean.append({"text": str(o.get("text", "未知任务"))[:60], "kind": kind,
                      "target": max(1, int(o.get("target", 1) or 1)), "progress": int(o.get("progress", 0) or 0)})
    c.execute("INSERT INTO daily_quests(date,objectives,completed) VALUES(?,?,0) "
              "ON CONFLICT(date) DO UPDATE SET objectives=excluded.objectives, completed=0",
              (date, json.dumps(clean, ensure_ascii=False)))
    return clean


def get_quest(c, date=None):
    r = c.execute("SELECT * FROM daily_quests WHERE date=?", (date or today(),)).fetchone()
    if not r:
        return None
    return {"date": r["date"], "objectives": json.loads(r["objectives"]), "completed": bool(r["completed"])}


def progress_quest(c, events, minutes=0, problems=0, done_idx=()):
    from . import db
    q = get_quest(c)
    if not q or q["completed"]:
        return
    for i, o in enumerate(q["objectives"]):
        if o["kind"] == "minutes":
            o["progress"] += minutes
        elif o["kind"] == "problems":
            o["progress"] += problems
        if i in done_idx:
            o["progress"] = o["target"]
    done = all(o["progress"] >= o["target"] for o in q["objectives"])
    c.execute("UPDATE daily_quests SET objectives=?, completed=? WHERE date=?",
              (json.dumps(q["objectives"], ensure_ascii=False), int(done), q["date"]))
    if done:
        b = buffs(c)
        reward = round(100 * (1 + b["quest"] / 100))
        p = db.player(c)
        db.update_player(c, quests_completed=p["quests_completed"] + 1)
        events.append({"type": "quest_complete", "points": reward})
        gain_points(c, reward, events)
        grant_chest(c, events, "每日任务")


# ---------------------------------------------------------------- 结算
def settle(c, events, action):
    """处理 AI / 演示模式给出的 award 动作。action 已经过初步校验。"""
    from . import db
    p = db.player(c)
    t = today()
    used = c.execute("SELECT COALESCE(SUM(base_points),0) s FROM logs WHERE date=?", (t,)).fetchone()["s"]
    remaining = max(0, DAILY_CAP - used)
    b = buffs(c, p)

    raw = []
    for item in action.get("breakdown") or []:
        try:
            pts = max(0, int(item.get("points", 0)))
        except (TypeError, ValueError):
            continue
        kind = item.get("kind") if item.get("kind") in ("time", "difficulty", "problem", "streak", "other") else "other"
        raw.append({"item": str(item.get("item", "奖励"))[:30], "points": pts, "kind": kind})
    if not raw:
        raw = [{"item": "修炼奖励", "points": max(0, int(action.get("points", 0) or 0)), "kind": "other"}]

    # 惩罚中：坚持奖励暂停
    if p["penalty_pending"]:
        for r in raw:
            if r["kind"] == "streak":
                r["points"] = 0
                r["item"] += "（惩罚中暂停）"

    base = sum(r["points"] for r in raw)
    if base > remaining:  # 按比例裁剪到每日上限
        ratio = remaining / base if base else 0
        for r in raw:
            r["points"] = int(r["points"] * ratio)
        base = sum(r["points"] for r in raw)

    lines = [dict(r) for r in raw]
    extra = 0
    for kind, key, label in (("time", "time", "力量/坦克加成"), ("problem", "problem", "智力/尖牙加成"), ("streak", "streak", "体力加成")):
        part = sum(r["points"] for r in raw if r["kind"] == kind)
        if part and b[key]:
            add = round(part * b[key] / 100)
            extra += add
            lines.append({"item": label, "points": add, "kind": "bonus"})
    if b["global"]:
        add = round((base + extra) * b["global"] / 100)
        extra += add
        lines.append({"item": "影子加成", "points": add, "kind": "bonus"})
    if b["boost_today"]:
        add = round((base + extra) * 0.5)
        extra += add
        lines.append({"item": "宝箱增益 x1.5", "points": add, "kind": "bonus"})
    total = base + extra

    minutes = max(0, int(action.get("minutes", 0) or 0))
    problems = max(0, int(action.get("problems", 0) or 0))

    # 连续天数 / 铁之盾
    streak = p["streak"]
    last = p["last_study_date"]
    shield_used = False
    if last != t:
        if last == (dt.date.today() - dt.timedelta(days=1)).isoformat():
            streak += 1
        elif last == (dt.date.today() - dt.timedelta(days=2)).isoformat() and b["iron_shield"]:
            streak += 1
            shield_used = True
        else:
            streak = 1
    fields = {"streak": streak, "last_study_date": t}
    if shield_used:
        fields["shield_week"] = week_key()
        events.append({"type": "shield", "text": "铁举起巨盾：断签已被抵挡，连续天数保留。"})
    db.update_player(c, **fields)

    if p["penalty_pending"] and minutes >= 30:
        db.update_player(c, penalty_pending=0)
        events.append({"type": "penalty_clear", "text": "惩罚任务完成，已脱离惩罚区域。"})

    c.execute("INSERT INTO logs(date,minutes,problems,points,base_points,summary,comment,breakdown) VALUES(?,?,?,?,?,?,?,?)",
              (t, minutes, problems, total, base, str(action.get("summary", ""))[:200],
               str(action.get("comment", ""))[:500], json.dumps(lines, ensure_ascii=False)))

    extra_flag = used > 0
    events.append({"type": "award", "points": total, "breakdown": lines, "summary": action.get("summary", ""),
                   "title": action.get("title"), "tomorrow_quest": action.get("tomorrow_quest"),
                   "capped": remaining < DAILY_CAP and remaining == base, "extra": extra_flag, "streak": streak})
    gain_points(c, total, events)

    if streak > 0 and streak % 7 == 0 and last != t:
        grant_chest(c, events, f"连续 {streak} 天")
    if random.random() < 0.10:
        grant_chest(c, events, "幸运掉落")

    progress_quest(c, events, minutes=minutes, problems=problems,
                   done_idx=tuple(i for i in (action.get("quest_done") or []) if isinstance(i, int)))

    if action.get("gate_id") and action.get("stage_cleared") is not None:
        clear_stage(c, events, int(action["gate_id"]), int(action["stage_cleared"]))
    check_achievements(c, events)


# ---------------------------------------------------------------- 召唤
def arise(c, events, soldier_id):
    from . import db
    s = SHADOW_BY_ID.get(soldier_id)
    if not s:
        return "不存在这个影子。"
    p = db.player(c)
    owned = army(c).get(soldier_id, 0)
    if owned and not s["repeat"]:
        return f"{s['name']} 已经在你的军团中了。"
    if p["points"] < s["cost"]:
        return f"积分不足：需要 {s['cost']}，当前 {p['points']}。"
    db.update_player(c, points=p["points"] - s["cost"])
    c.execute("INSERT INTO army(soldier_id,count) VALUES(?,1) ON CONFLICT(soldier_id) DO UPDATE SET count=count+1", (soldier_id,))
    events.append({"type": "arise", "soldier": s, "count": owned + 1})
    check_achievements(c, events)
    return None


# ---------------------------------------------------------------- 副本
def create_gate(c, events, name, rank, stages, exam_date=None):
    rank = rank if rank in GATE_REWARD else "C"
    stages = [str(s)[:40] for s in (stages or []) if str(s).strip()][:8]
    if not stages:
        stages = ["第一层：基础概念", "第二层：核心知识", "第三层：重点难点", "第四层：综合练习", "第五层：模拟冲刺"]
    cur = c.execute("INSERT INTO gates(name,rank,exam_date) VALUES(?,?,?)", (str(name)[:40], rank, exam_date))
    gid = cur.lastrowid
    for i, s in enumerate(stages):
        c.execute("INSERT INTO gate_stages(gate_id,idx,name,is_boss) VALUES(?,?,?,0)", (gid, i, s))
    c.execute("INSERT INTO gate_stages(gate_id,idx,name,is_boss) VALUES(?,?,?,1)", (gid, len(stages), f"Boss：{name}"))
    events.append({"type": "gate_open", "gate_id": gid, "name": name, "rank": rank})
    return gid


def gates(c):
    out = []
    for g in c.execute("SELECT * FROM gates ORDER BY cleared, id DESC"):
        g = dict(g)
        g["stages"] = [dict(s) for s in c.execute("SELECT * FROM gate_stages WHERE gate_id=? ORDER BY idx", (g["id"],))]
        if g["exam_date"]:
            try:
                g["days_left"] = (dt.date.fromisoformat(g["exam_date"]) - dt.date.today()).days
            except ValueError:
                g["days_left"] = None
        out.append(g)
    return out


def clear_stage(c, events, gate_id, idx):
    from . import db
    g = c.execute("SELECT * FROM gates WHERE id=?", (gate_id,)).fetchone()
    s = c.execute("SELECT * FROM gate_stages WHERE gate_id=? AND idx=?", (gate_id, idx)).fetchone()
    if not g or not s or s["cleared"]:
        return "关卡不存在或已通关。"
    b = buffs(c)
    reward = GATE_REWARD[g["rank"]]
    if s["is_boss"]:
        reward *= 5
        if b["boss_double"]:
            reward *= 2
    reward = round(reward * (1 + b["gate"] / 100))
    c.execute("UPDATE gate_stages SET cleared=1 WHERE id=?", (s["id"],))
    events.append({"type": "stage_clear", "gate": g["name"], "stage": s["name"], "boss": bool(s["is_boss"]), "points": reward})
    gain_points(c, reward, events)
    left = c.execute("SELECT COUNT(*) n FROM gate_stages WHERE gate_id=? AND cleared=0", (gate_id,)).fetchone()["n"]
    if left == 0:
        c.execute("UPDATE gates SET cleared=1 WHERE id=?", (gate_id,))
        title = f"{g['name']}征服者"
        events.append({"type": "gate_clear", "gate": g["name"], "rank": g["rank"], "title": title})
        db.update_player(c, title=title)
        grant_chest(c, events, "Boss 战")
    check_achievements(c, events)
    return None


# ---------------------------------------------------------------- 宝箱
def grant_chest(c, events, source):
    tier = random.choices(["普通", "稀有", "传说"], weights=[70, 25, 5])[0]
    cur = c.execute("INSERT INTO chests(tier,source) VALUES(?,?)", (tier, source))
    events.append({"type": "chest_get", "id": cur.lastrowid, "tier": tier, "source": source})


def open_chest(c, events, chest_id):
    from . import db
    ch = c.execute("SELECT * FROM chests WHERE id=? AND opened=0", (chest_id,)).fetchone()
    if not ch:
        return "宝箱不存在或已开启。"
    roll = random.random()
    tier = ch["tier"]
    if roll < 0.6:
        lo, hi = {"普通": (50, 150), "稀有": (200, 400), "传说": (800, 1500)}[tier]
        content = {"kind": "points", "amount": random.randint(lo, hi)}
    elif roll < 0.85:
        content = {"kind": "attr", "amount": {"普通": 1, "稀有": 2, "传说": 3}[tier]}
    else:
        content = {"kind": "boost"}
    c.execute("UPDATE chests SET opened=1, content=? WHERE id=?", (json.dumps(content), chest_id))
    p = db.player(c)
    if tier == "传说":
        c.execute("INSERT OR IGNORE INTO achievements(id,unlocked_at) VALUES('legend_chest',datetime('now','localtime'))")
        events.append({"type": "achievement", "id": "legend_chest", "name": "天选之人"})
    events.append({"type": "chest_open", "tier": tier, "content": content})
    if content["kind"] == "points":
        gain_points(c, content["amount"], events)
    elif content["kind"] == "attr":
        db.update_player(c, attr_points=p["attr_points"] + content["amount"])
    else:
        tomorrow = (dt.date.today() + dt.timedelta(days=1)).isoformat()
        db.update_player(c, boost_date=tomorrow)
    return None


def chests(c):
    return [dict(r) for r in c.execute("SELECT * FROM chests WHERE opened=0 ORDER BY id")]


# ---------------------------------------------------------------- 属性
def allocate(c, alloc):
    from . import db
    p = db.player(c)
    total = sum(max(0, int(v)) for v in alloc.values())
    if total > p["attr_points"]:
        return "属性点不足。"
    at = p["attrs"]
    for k, v in alloc.items():
        if k in ATTRS:
            at[k] = min(ATTR_CAP, at.get(k, 0) + max(0, int(v)))
    db.update_player(c, attrs=at, attr_points=p["attr_points"] - total)
    return None


# ---------------------------------------------------------------- 成就
def check_achievements(c, events):
    from . import db
    p = db.player(c)
    a = army(c)
    have = {r["id"] for r in c.execute("SELECT id FROM achievements")}
    mins = c.execute("SELECT COALESCE(SUM(minutes),0) m FROM logs").fetchone()["m"]
    nlogs = c.execute("SELECT COUNT(*) n FROM logs").fetchone()["n"]
    cleared = c.execute("SELECT COUNT(*) n FROM gates WHERE cleared=1").fetchone()["n"]
    s_cleared = c.execute("SELECT COUNT(*) n FROM gates WHERE cleared=1 AND rank='S'").fetchone()["n"]
    cond = {
        "first_award": nlogs >= 1, "streak7": p["streak"] >= 7, "streak30": p["streak"] >= 30,
        "hours10": mins >= 600, "hours100": mins >= 6000, "first_shadow": sum(a.values()) >= 1,
        "igris": bool(a.get("igris")), "beru": bool(a.get("beru")), "bellion": bool(a.get("bellion")),
        "first_gate": cleared >= 1, "s_boss": s_cleared >= 1, "lv10": p["level"] >= 10, "lv30": p["level"] >= 30,
        "quest10": p["quests_completed"] >= 10,
    }
    names = {i: n for i, n, _ in ACHIEVEMENTS}
    for k, ok in cond.items():
        if ok and k not in have:
            c.execute("INSERT INTO achievements(id,unlocked_at) VALUES(?,datetime('now','localtime'))", (k,))
            events.append({"type": "achievement", "id": k, "name": names[k]})


def achievements(c):
    have = {r["id"]: r["unlocked_at"] for r in c.execute("SELECT * FROM achievements")}
    return [{"id": i, "name": n, "desc": d, "unlocked_at": have.get(i)} for i, n, d in ACHIEVEMENTS]


# ---------------------------------------------------------------- 总状态
def full_state(c):
    from . import db
    p = db.player(c)
    b = buffs(c, p)
    a = army(c)
    power = sum(SHADOW_BY_ID[k]["power"] * v for k, v in a.items() if k in SHADOW_BY_ID)
    t = today()
    today_base = c.execute("SELECT COALESCE(SUM(base_points),0) s FROM logs WHERE date=?", (t,)).fetchone()["s"]
    return {
        "player": {**p, "rank_title": title_for_level(p["level"]),
                   "xp_cur": xp_for_level(p["level"]), "xp_next": xp_for_level(p["level"] + 1)},
        "buffs": b, "buff_labels": buff_labels(b),
        "army": a, "army_power": power,
        "shop": SHADOWS,
        "quest": get_quest(c),
        "gates": gates(c),
        "chests": chests(c),
        "achievements": achievements(c),
        "today_base": today_base, "daily_cap": DAILY_CAP,
        "attr_names": ATTRS,
    }


def ai_state(c):
    """发给 AI 的精简状态。"""
    s = full_state(c)
    p = s["player"]
    return {
        "date": today(), "name": p["name"], "level": p["level"], "rank": p["rank_title"],
        "points": p["points"], "streak": p["streak"], "penalty_pending": bool(p["penalty_pending"]),
        "today_points_used": s["today_base"], "daily_cap": DAILY_CAP,
        "buffs": s["buff_labels"],
        "army": {SHADOW_BY_ID[k]["name"]: v for k, v in s["army"].items() if k in SHADOW_BY_ID},
        "shop": [{"id": x["id"], "name": x["name"], "cost": x["cost"], "repeatable": x["repeat"],
                  "owned": s["army"].get(x["id"], 0)} for x in SHADOWS],
        "today_quest": s["quest"],
        "gates": [{"id": g["id"], "name": g["name"], "rank": g["rank"], "exam_date": g["exam_date"],
                   "stages": [{"idx": st["idx"], "name": st["name"], "boss": bool(st["is_boss"]), "cleared": bool(st["cleared"])}
                              for st in g["stages"]]} for g in s["gates"] if not g["cleared"]],
    }

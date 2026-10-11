"""AI 系统：OpenAI 兼容接口 + 本地演示模式。"""
import json
import re

import httpx

from . import game

ACTION_RE = re.compile(r"<action>([\s\S]*?)</action>", re.I)

SYSTEM_PROMPT = """你是《我独自升级》中的「系统」，正在辅助玩家通过学习变强。你的说话风格：冷静、简洁、像游戏系统提示，偶尔带一点鼓励，用中文，常以【系统】开头。

你的职责：
1. 玩家会和你聊今天学了什么。如果信息不够（学了多久、学了什么、遇到什么困难、攻克了什么难题），自然地追问，一次只问一两个问题。可以给简短的学习建议。
2. 信息足够后，进行结算。评分规则（公平、不注水）：
   - 时长分(kind=time)：专注学习约每 30 分钟 10 分；
   - 难度加成(kind=difficulty)：根据内容难度，最多为时长分的 50%；
   - 难题奖励(kind=problem)：每道真正攻克的难题 20~100 分；
   - 坚持奖励(kind=streak)：根据连续天数 streak 给 5~50 分；
   - 每日基础分上限 daily_cap，已用 today_points_used；如今天已经结算过，只结算新增的学习。
   - 敷衍或几乎没学习：给很少的分，并调侃“惩罚区域”。永远不扣分。
   - 影子加成、属性加成由程序自动计算，你不要重复计算。
3. 玩家想召唤影子时，检查 points 是否足够、不可重复的影子是否已拥有。足够才执行，否则拒绝并告诉还差多少。
4. 玩家想把一门课/一场考试做成副本时，帮他拆成 4~6 个关卡（最后的 Boss 由程序自动添加），根据难度定 E/D/C/B/A/S 级。
5. 玩家说完成了某个副本关卡时，可以在结算里带上 gate_id 和 stage_cleared（关卡 idx），或单独用 clear_stage 动作。

需要程序执行操作时，在回复最后附加一个或多个动作块，格式严格为 <action>{JSON}</action>，JSON 之外不要多写：
- 结算：{"type":"award","breakdown":[{"item":"时长分","points":40,"kind":"time"}],"minutes":120,"problems":1,"summary":"一句话总结今天的修炼","comment":"系统评语","title":"可选的称号或null","tomorrow_quest":"明日紧急任务建议","quest_done":[可选,今日任务中kind=other且已完成的序号],"gate_id":可选,"stage_cleared":可选}
- 召唤：{"type":"arise","soldier_id":"igris"}
- 发布今日任务（仅当玩家要求换任务时）：{"type":"daily_quest","objectives":[{"text":"专注学习90分钟","kind":"minutes","target":90},{"text":"攻克1道难题","kind":"problems","target":1},{"text":"复习昨天内容","kind":"other","target":1}]}
- 创建副本：{"type":"create_gate","name":"高数期末","rank":"A","exam_date":"2026-12-20或null","stages":["极限与连续","导数与微分","积分","微分方程"]}
- 通关关卡：{"type":"clear_stage","gate_id":1,"stage_idx":0}

动作块不会显示给玩家，所以回复正文里要自然地说明结果。下面是玩家当前状态(JSON)：
"""


def parse_actions(text):
    actions = []
    for m in ACTION_RE.finditer(text):
        raw = m.group(1).strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw).strip()
        try:
            actions.append(json.loads(raw))
        except json.JSONDecodeError:
            s, e = raw.find("{"), raw.rfind("}")
            if s != -1 and e > s:
                try:
                    actions.append(json.loads(raw[s:e + 1]))
                except json.JSONDecodeError:
                    pass
    clean = ACTION_RE.sub("", text).strip()
    return clean, actions


def _headers(key):
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


async def list_models(base_url, key):
    async with httpx.AsyncClient(timeout=20) as cli:
        r = await cli.get(base_url.rstrip("/") + "/models", headers=_headers(key))
        r.raise_for_status()
        data = r.json()
        items = data.get("data", data if isinstance(data, list) else [])
        return sorted({m.get("id") for m in items if isinstance(m, dict) and m.get("id")})


async def chat(base_url, key, model, state, history):
    msgs = [{"role": "system", "content": SYSTEM_PROMPT + json.dumps(state, ensure_ascii=False)}]
    msgs += history
    async with httpx.AsyncClient(timeout=90) as cli:
        r = await cli.post(base_url.rstrip("/") + "/chat/completions", headers=_headers(key),
                           json={"model": model, "messages": msgs, "temperature": 0.7})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------- 演示模式
CN_NUM = {"零": 0, "一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "半": 0.5}


def _cn(s):
    if s in CN_NUM:
        return CN_NUM[s]
    if s.startswith("十"):
        return 10 + CN_NUM.get(s[1:], 0)
    if "十" in s:
        a, b = s.split("十", 1)
        return CN_NUM.get(a, 1) * 10 + CN_NUM.get(b, 0)
    return None


def parse_minutes(text):
    total, found = 0.0, False
    for num, unit in re.findall(r"(\d+(?:\.\d+)?|[一二两三四五六七八九十半]+)\s*(个半小时|个小时|小时|h|hr|分钟|min|m\b)", text, re.I):
        v = float(num) if num[0].isdigit() else _cn(num)
        if v is None:
            continue
        found = True
        if unit == "个半小时":
            total += (v + 0.5) * 60
        elif unit.lower() in ("个小时", "小时", "h", "hr"):
            total += v * 60
        else:
            total += v
    if "半小时" in text and not re.search(r"\d\s*个半小时", text) and "个半小时" not in text:
        total += 30
        found = True
    return int(total) if found else None


def parse_problems(text):
    if re.search(r"没有?(攻克|解决|难题)|无难题|没啥难", text):
        return 0
    m = re.search(r"(\d+|[一二两三四五六七八九十]+)\s*(道|个)\s*(难题|题)", text)
    if m:
        n = m.group(1)
        return int(n) if n.isdigit() else int(_cn(n) or 1)
    if re.search(r"攻克|解决了|搞懂|做出来|难题", text):
        return 1
    return None


def demo_reply(c, text, ctx):
    """返回 (回复文本, 动作列表, 新的 ctx)。ctx 保存多轮收集的信息。"""
    s = game.ai_state(c)
    t = text.strip()

    m = re.search(r"(召唤|唤醒|arise|ARISE)\s*(.+)", t)
    if m:
        name = m.group(2).strip()
        for sh in game.SHADOWS:
            if sh["id"].lower() in name.lower() or sh["name"].split(" ")[0] in name:
                return f"【系统】正在检测影子：{sh['name']}……", [{"type": "arise", "soldier_id": sh["id"]}], ctx
        names = "、".join(x["name"].split(" ")[0] for x in game.SHADOWS)
        return f"【系统】未识别的影子。可召唤：{names}。", [], ctx

    if re.search(r"状态|属性|我的信息", t):
        army = "、".join(f"{k}×{v}" for k, v in s["army"].items()) or "暂无"
        return (f"【系统】玩家：{s['name']}｜等级 {s['level']}（{s['rank']}）｜积分 {s['points']}｜连续 {s['streak']} 天\n"
                f"影子军团：{army}\n当前加成：{'；'.join(s['buffs']) or '无'}"), [], ctx

    m = re.search(r"把?(.+?)(建成|做成|创建)副本", t)
    if m:
        name = m.group(1).strip("把 ") or "新副本"
        rank = "S" if re.search(r"期末|考研|高考|雅思|托福", name) else "B"
        return (f"【系统】检测到新的传送门：{name}（{rank}级）。已拆分为 5 层关卡，最终 Boss 为考试本身。"), \
               [{"type": "create_gate", "name": name, "rank": rank, "stages": []}], ctx

    if re.search(r"汇报|今天学|学了|学习了|复习|刷题|看了|写了|做了", t) or ctx.get("collecting"):
        ctx = dict(ctx)
        ctx["collecting"] = True
        ctx["content"] = (ctx.get("content", "") + " " + t).strip()
        mins = parse_minutes(t)
        if mins is not None:
            ctx["minutes"] = mins
        probs = parse_problems(t)
        if probs is not None:
            ctx["problems"] = probs
        if re.search(r"困难|卡住|不会|难点|难理解|搞不懂", t):
            ctx["difficulty"] = True
        if "minutes" not in ctx:
            return "【系统】已记录修炼内容。请报告本次专注学习时长。（例：2小时30分钟）", [], ctx
        if "problems" not in ctx and not ctx.get("asked_problem"):
            ctx["asked_problem"] = True
            return "【系统】时长已确认。遇到了什么困难？是否攻克了难题？", [], ctx
        minutes = ctx["minutes"]
        problems = ctx.get("problems", 0) or 0
        tp = round(minutes / 30 * 10)
        dp = round(tp * (0.3 if ctx.get("difficulty") else 0.1))
        pp = problems * 50
        sp = min(50, 5 + s["streak"] * 5)
        breakdown = [{"item": "时长分", "points": tp, "kind": "time"},
                     {"item": "难度加成", "points": dp, "kind": "difficulty"}]
        if pp:
            breakdown.append({"item": f"难题奖励 ×{problems}", "points": pp, "kind": "problem"})
        breakdown.append({"item": "坚持奖励", "points": sp, "kind": "streak"})
        if minutes < 20:
            comment = "【系统】修炼量过低。再这样下去，你会被传送到惩罚区域。"
        elif minutes >= 180:
            comment = "【系统】惊人的专注力。你正在接近极限，然后突破它。"
        else:
            comment = "【系统】每日修炼完成。变强的路上，没有捷径。"
        action = {"type": "award", "breakdown": breakdown, "minutes": minutes, "problems": problems,
                  "summary": ctx["content"][:60], "comment": comment,
                  "title": "难题猎手" if problems >= 2 else None,
                  "tomorrow_quest": "专注学习 90 分钟，并复习今天的难点。"}
        return comment, [action], {}

    return ("【系统】我在。你可以：汇报今天的学习 / 说“召唤 伊格里斯” / 说“把高数期末建成副本” / 查看状态。"), [], ctx

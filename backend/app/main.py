"""FastAPI 入口。运行：uvicorn app.main:app --reload --port 8000"""
import json
import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import ai, db, game

app = FastAPI(title="影子军团学习系统")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _startup():
    db.init()


# ---------------------------------------------------------------- helpers
def _messages(c, limit=200):
    rows = c.execute("SELECT * FROM (SELECT * FROM messages ORDER BY id DESC LIMIT ?) ORDER BY id", (limit,)).fetchall()
    return [{"id": r["id"], "role": r["role"], "content": r["content"], "cards": json.loads(r["cards"]),
             "created_at": r["created_at"]} for r in rows]


def _add_msg(c, role, content, cards=None):
    cur = c.execute("INSERT INTO messages(role,content,cards) VALUES(?,?,?)",
                    (role, content, json.dumps(cards or [], ensure_ascii=False)))
    r = c.execute("SELECT * FROM messages WHERE id=?", (cur.lastrowid,)).fetchone()
    return {"id": r["id"], "role": r["role"], "content": r["content"], "cards": cards or [], "created_at": r["created_at"]}


def _settings(c):
    return {"base_url": db.get_setting(c, "base_url", "https://api.openai.com/v1"),
            "api_key": db.get_setting(c, "api_key", ""),
            "model": db.get_setting(c, "model", ""),
            "demo": db.get_setting(c, "demo", "1") == "1"}


def _tick(c):
    events = []
    game.daily_tick(c, events)
    msgs = []
    for e in events:
        if e["type"] == "quest":
            lines = "\n".join(f"· {o['text']}" for o in e["objectives"])
            msgs.append(_add_msg(c, "assistant", f"【系统】每日任务已发布：\n{lines}\n完成全部任务可获得奖励与宝箱。", [e]))
        elif e["type"] in ("penalty", "pardon"):
            msgs.append(_add_msg(c, "assistant", f"【警告】{e['text']}" + (f"\n{e['task']}" if e.get("task") else ""), [e]))
    return events


def apply_actions(c, actions, events):
    errors = []
    for a in actions:
        if not isinstance(a, dict):
            continue
        t = a.get("type")
        if t == "award":
            game.settle(c, events, a)
        elif t == "arise":
            err = game.arise(c, events, str(a.get("soldier_id", "")))
            if err:
                errors.append(err)
        elif t == "daily_quest" and isinstance(a.get("objectives"), list):
            objs = game.set_quest(c, game.today(), a["objectives"])
            events.append({"type": "quest", "objectives": objs})
        elif t == "create_gate":
            game.create_gate(c, events, a.get("name", "新副本"), a.get("rank", "C"), a.get("stages"), a.get("exam_date"))
        elif t == "clear_stage":
            err = game.clear_stage(c, events, int(a.get("gate_id", 0)), int(a.get("stage_idx", -1)))
            if err:
                errors.append(err)
    return errors


# ---------------------------------------------------------------- state
@app.get("/api/state")
def get_state():
    with db.tx() as c:
        events = _tick(c)
        s = game.full_state(c)
        st = _settings(c)
        s["settings"] = {**st, "api_key": "", "has_key": bool(st["api_key"])}
        s["messages"] = _messages(c)
        s["events"] = events
        s["logs"] = [dict(r, breakdown=json.loads(r["breakdown"])) for r in
                     c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 100")]
        return s


class PlayerIn(BaseModel):
    name: str | None = None
    accepted: bool | None = None
    title: str | None = None


@app.put("/api/player")
def put_player(body: PlayerIn):
    with db.tx() as c:
        f = {}
        if body.name is not None:
            f["name"] = body.name[:20] or "猎人"
        if body.accepted is not None:
            f["accepted"] = int(body.accepted)
        if body.title is not None:
            f["title"] = body.title[:30] or None
        if f:
            db.update_player(c, **f)
    return {"ok": True}


# ---------------------------------------------------------------- settings
class SettingsIn(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    demo: bool | None = None


@app.put("/api/settings")
def put_settings(body: SettingsIn):
    with db.tx() as c:
        if body.base_url is not None:
            db.set_setting(c, "base_url", body.base_url.strip())
        if body.api_key:  # 空字符串表示不修改
            db.set_setting(c, "api_key", body.api_key.strip())
        if body.model is not None:
            db.set_setting(c, "model", body.model.strip())
        if body.demo is not None:
            db.set_setting(c, "demo", "1" if body.demo else "0")
    return {"ok": True}


class ModelsIn(BaseModel):
    base_url: str | None = None
    api_key: str | None = None


@app.post("/api/models")
async def models(body: ModelsIn):
    with db.tx() as c:
        st = _settings(c)
    base = body.base_url or st["base_url"]
    key = body.api_key or st["api_key"]
    if not key:
        raise HTTPException(400, "请先填写 API Key")
    try:
        return {"models": await ai.list_models(base, key)}
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"拉取失败：HTTP {e.response.status_code}")
    except Exception as e:  # noqa
        raise HTTPException(502, f"拉取失败：{e}")


# ---------------------------------------------------------------- chat
class ChatIn(BaseModel):
    text: str


@app.post("/api/chat")
async def chat(body: ChatIn):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "内容为空")
    with db.tx() as c:
        events = _tick(c)
        user_msg = _add_msg(c, "user", text)
        st = _settings(c)
        use_demo = st["demo"] or not (st["api_key"] and st["model"])
        state = game.ai_state(c)
        history = [{"role": m["role"], "content": m["content"]} for m in _messages(c, 30)]
        demo_ctx = json.loads(db.get_setting(c, "demo_ctx", "{}"))

    if use_demo:
        with db.tx() as c:
            reply, actions, new_ctx = ai.demo_reply(c, text, demo_ctx)
            db.set_setting(c, "demo_ctx", json.dumps(new_ctx, ensure_ascii=False))
    else:
        try:
            raw = await ai.chat(st["base_url"], st["api_key"], st["model"], state, history)
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            msg = {401: "API Key 无效", 404: "接口地址或模型不存在", 429: "请求过于频繁或额度不足"}.get(code, f"HTTP {code}")
            raise HTTPException(502, f"系统连接失败：{msg}")
        except Exception as e:  # noqa
            raise HTTPException(502, f"系统连接失败：{e}")
        reply, actions = ai.parse_actions(raw)

    with db.tx() as c:
        errs = apply_actions(c, actions, events)
        if errs:
            reply += "\n" + "\n".join(f"【系统】操作失败：{e}" for e in errs)
        bot = _add_msg(c, "assistant", reply or "【系统】……", events)
    return {"user": user_msg, "reply": bot, "events": events}


@app.delete("/api/messages")
def clear_messages():
    with db.tx() as c:
        c.execute("DELETE FROM messages")
        db.set_setting(c, "demo_ctx", "{}")
    return {"ok": True}


# ---------------------------------------------------------------- 直接操作
@app.post("/api/arise/{soldier_id}")
def arise(soldier_id: str):
    with db.tx() as c:
        events = []
        err = game.arise(c, events, soldier_id)
        if err:
            raise HTTPException(400, err)
        return {"events": events}


class AllocIn(BaseModel):
    alloc: dict[str, int]


@app.post("/api/attrs")
def attrs(body: AllocIn):
    with db.tx() as c:
        err = game.allocate(c, body.alloc)
        if err:
            raise HTTPException(400, err)
    return {"ok": True}


@app.post("/api/chests/{chest_id}/open")
def open_chest(chest_id: int):
    with db.tx() as c:
        events = []
        err = game.open_chest(c, events, chest_id)
        if err:
            raise HTTPException(400, err)
        return {"events": events}


class GateIn(BaseModel):
    name: str
    rank: str = "C"
    exam_date: str | None = None
    stages: list[str] = []


@app.post("/api/gates")
def new_gate(body: GateIn):
    with db.tx() as c:
        events = []
        game.create_gate(c, events, body.name, body.rank, body.stages, body.exam_date or None)
        return {"events": events}


@app.post("/api/gates/{gate_id}/stages/{idx}/clear")
def clear_stage(gate_id: int, idx: int):
    with db.tx() as c:
        events = []
        err = game.clear_stage(c, events, gate_id, idx)
        if err:
            raise HTTPException(400, err)
        return {"events": events}


@app.delete("/api/gates/{gate_id}")
def del_gate(gate_id: int):
    with db.tx() as c:
        c.execute("DELETE FROM gates WHERE id=?", (gate_id,))
    return {"ok": True}


@app.post("/api/quest/{idx}/done")
def quest_done(idx: int):
    with db.tx() as c:
        events = []
        game.progress_quest(c, events, done_idx=(idx,))
        return {"events": events}


# ---------------------------------------------------------------- 存档
TABLES = ["player", "settings", "messages", "logs", "army", "daily_quests", "gates", "gate_stages", "chests", "achievements"]


@app.get("/api/export")
def export():
    with db.tx() as c:
        data = {t: [dict(r) for r in c.execute(f"SELECT * FROM {t}")] for t in TABLES}
        data["settings"] = [r for r in data["settings"] if r["key"] != "api_key"]
        return {"version": 1, "data": data}


class ImportIn(BaseModel):
    version: int
    data: dict


@app.post("/api/import")
def import_(body: ImportIn):
    with db.tx() as c:
        for t in reversed(TABLES):
            if t in body.data:
                if t == "settings":
                    c.execute("DELETE FROM settings WHERE key!='api_key'")
                else:
                    c.execute(f"DELETE FROM {t}")
        for t in TABLES:
            for row in body.data.get(t, []):
                if t == "settings" and row.get("key") == "api_key":
                    continue
                cols = ",".join(row.keys())
                qs = ",".join("?" * len(row))
                c.execute(f"INSERT OR REPLACE INTO {t}({cols}) VALUES({qs})", tuple(row.values()))
    return {"ok": True}


@app.post("/api/debug/points")
def debug_points():
    with db.tx() as c:
        events = []
        game.gain_points(c, 1000, events)
        return {"events": events}


# ---------------------------------------------------------------- 生产环境：托管前端构建产物
DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = os.path.join(DIST, path)
        return FileResponse(f if path and os.path.isfile(f) else os.path.join(DIST, "index.html"))

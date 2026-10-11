# 影子军团学习系统 · Shadow Army Study System

《我独自升级》风格的学习激励系统。每天和「系统」聊你学了什么、学了多久、遇到什么困难、攻克了什么难题，AI 会给你结算积分；积分可以唤醒程肖宇的影子士兵（伊格里斯、贝尔、贝利昂……）。

**技术栈**：React 18 + Vite（前端） · Python FastAPI（后端） · SQLite（存储）

## 功能

- **与系统对话**：聊天式汇报，系统会追问时长和难题，聊够了自动结算并弹出结算卡；说"召唤伊格里斯"也能直接 ARISE
- **AI 设置**：填写任意 OpenAI 兼容接口的 Base URL 与 Key，一键拉取模型列表；未配置时使用**演示模式**（本地规则评分）
- **每日任务 + 惩罚区域**：每天自动发布 3 个任务，完成得奖励和宝箱；没完成第二天进入惩罚区域（不扣分，坚持奖励暂停，直到完成惩罚任务）
- **传送门副本**：把一门课或一场考试建成 E~S 级副本，分关卡攻略，考试是 Boss 战
- **影子技能**：每个影子都有被动加成（伊格里斯全部积分 +10%、铁每周一次断签保护、贝尔免除惩罚……）
- **属性点**：升级获得属性点，分配到力量 / 敏捷 / 智力 / 体力 / 感知，影响结算
- **宝箱 / 成就称号 / 音效**：三档宝箱、15 个可装备的称号、Web Audio 合成音效
- **修炼记录**：14 天积分柱状图与历史
- **存档导入导出**（导出不含 API Key）

## 本地运行

需要 Python 3.10+ 和 Node.js 18+。

```bash
# 1. 后端
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. 前端（另开一个终端）
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 。前端开发服务器会把 `/api` 代理到 8000 端口。

### 单端口运行

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --port 8000
```

打开 http://localhost:8000 ，后端直接托管构建好的前端。

## 接入 AI

进入「AI 设置」：

1. 填写 Base URL（如 `https://api.openai.com/v1`、`https://api.deepseek.com/v1`、本地 Ollama `http://localhost:11434/v1` 等 OpenAI 兼容接口）
2. 填写 API Key，点「拉取模型」，选择模型
3. 关闭「演示模式」，保存

Key 保存在本机 `backend/shadow.db`，只由后端转发给你填写的接口。

## 积分规则（默认）

| 项目 | 规则 |
|---|---|
| 时长分 | 约每 30 分钟专注学习 10 分 |
| 难度加成 | 最多为时长分的 50% |
| 难题奖励 | 每道真正攻克的难题 20~100 分 |
| 坚持奖励 | 依连续天数 5~50 分 |
| 每日上限 | 基础分 500（影子与属性加成另算） |

## 目录结构

```
backend/app/
  main.py   FastAPI 路由
  game.py   游戏规则（等级、影子、加成、任务、副本、宝箱、成就）
  ai.py     AI 接入、系统提示词、动作解析、演示模式
  db.py     SQLite 结构
frontend/src/
  App.jsx       页面与演出调度
  components/   聊天、任务、副本、商店、军团、状态、成就、记录、设置、演出
  sound.js      合成音效
```

## AI 动作协议

AI 在回复末尾附加 `<action>{JSON}</action>`，后端解析、校验后执行：
`award` 结算积分 · `arise` 召唤影子 · `daily_quest` 换今日任务 · `create_gate` 创建副本 · `clear_stage` 通关关卡。
详见 `backend/app/ai.py` 的 `SYSTEM_PROMPT`。

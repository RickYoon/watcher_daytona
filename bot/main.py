"""WatchBox — Telegram bot. /watch <natural language> spawns one Daytona sandbox per watch."""
import json, os, sys, time, logging
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "watchers"))
import brain, factory
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ["TG_BOT_TOKEN"]
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watches.json")
MAX_PER_USER = 3
SANDBOX_USD_PER_H = 0.0504 + 0.0162  # 1 vCPU + 1 GiB (daytona.io/pricing)

def load(): return json.load(open(DB)) if os.path.exists(DB) else {}
def save(d): json.dump(d, open(DB, "w"), ensure_ascii=False, indent=1)

async def cmd_watch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    text = " ".join(c.args).strip()
    if not text:
        return await u.message.reply_text("사용법: /watch 삼성전자 HBM 관련 부정적 뉴스 뜨면 알려줘")
    db = load(); mine = [w for w in db.values() if w["chat_id"] == u.effective_chat.id]
    if len(mine) >= MAX_PER_USER:
        return await u.message.reply_text(f"감시는 {MAX_PER_USER}개까지. /stop <id> 후 다시.")
    msg = await u.message.reply_text("🧠 의도 파싱 중…")
    try:
        spec = brain.parse_intent(text)
    except Exception as e:
        return await msg.edit_text(f"LLM 실패: {e}")
    wid = str(max([int(k) for k in db] + [0]) + 1)
    spec.update({"id": wid, "chat_id": u.effective_chat.id, "tg_token": TOKEN, "request": text})
    await msg.edit_text(f"🧠 {spec['type']} · {spec.get('query')} · {spec.get('interval_min')}분 [{spec['_model']}]\n📦 Daytona 샌드박스 생성 중…")
    try:
        info = factory.spawn(spec)
    except Exception as e:
        return await msg.edit_text(f"샌드박스 실패: {e}")
    spec.update(info); spec["started"] = time.time(); spec.pop("tg_token", None)
    db[wid] = spec; save(db)
    await msg.edit_text(
        f"✅ 감시 #{wid} 시작\n"
        f"유형 {spec['type']} · 대상 {spec.get('query')} · {spec.get('interval_min')}분마다\n"
        f"조건: {spec.get('condition')}\n"
        f"📦 sandbox {info['sandbox_id'][:8]} · 생성 {info['create_s']}s · 준비 {info['total_s']}s\n"
        f"💰 ≈ ${SANDBOX_USD_PER_H*24:.2f}/일")

async def cmd_list(u: Update, c):
    db = load(); mine = [w for w in db.values() if w["chat_id"] == u.effective_chat.id]
    if not mine: return await u.message.reply_text("감시 없음. /watch 로 시작")
    lines = []
    for w in mine:
        h = (time.time() - w["started"]) / 3600
        lines.append(f"#{w['id']} {w['type']} · {w.get('query')} · {h*60:.0f}분 경과 · ${h*SANDBOX_USD_PER_H:.4f}")
    await u.message.reply_text("\n".join(lines))

def _get(u, c):
    db = load(); wid = c.args[0] if c.args else None
    w = db.get(wid)
    return (db, w) if w and w["chat_id"] == u.effective_chat.id else (db, None)

async def cmd_stop(u: Update, c):
    db, w = _get(u, c)
    if not w: return await u.message.reply_text("/stop <id>")
    factory.stop(w["sandbox_id"]); del db[w["id"]]; save(db)
    await u.message.reply_text(f"🗑 감시 #{w['id']} 종료, 샌드박스 삭제")

async def cmd_logs(u: Update, c):
    db, w = _get(u, c)
    if not w: return await u.message.reply_text("/logs <id>")
    await u.message.reply_text(factory.logs(w["sandbox_id"])[-3500:])

async def cmd_test(u: Update, c):
    db, w = _get(u, c)
    if not w: return await u.message.reply_text("/test <id>")
    msg = await u.message.reply_text("🔎 샌드박스에서 최신 5건 즉시 판정 중…")
    await msg.edit_text(f"감시 #{w['id']} · 조건: {w.get('condition')}\n\n" + factory.test(w["sandbox_id"]))

async def cmd_help(u: Update, c):
    await u.message.reply_text("WatchBox — 말로 만드는 감시봇\n/watch <조건> · /list · /test <id> · /logs <id> · /stop <id>\n감시 1개 = Daytona 샌드박스 1개 · 판정 = Nosana LLM")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    for n, f in [("watch", cmd_watch), ("list", cmd_list), ("stop", cmd_stop), ("logs", cmd_logs), ("test", cmd_test), ("start", cmd_help), ("help", cmd_help)]:
        app.add_handler(CommandHandler(n, f))
    app.run_polling()

import json
from telegram import Update
from telegram.ext import (Application, CommandHandler, MessageHandler,
    filters, ContextTypes, TypeHandler, ApplicationHandlerStop)
from config import TG_TOKEN, OWNER_ID, MEMORY_DIR, MODEL, API_BASE, SYSTEM_PROMPT
from agent import run_agent

def mem_path(cid): return MEMORY_DIR / f"{cid}.json"

def load_history(cid):
    p = mem_path(cid)
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: pass
    return [{"role": "system", "content": SYSTEM_PROMPT}]

def save_history(cid, hist):
    trimmed = [hist[0]] + [m for m in hist[1:] if m.get("role") in ("user","assistant")][-40:]
    mem_path(cid).write_text(json.dumps(trimmed, ensure_ascii=False, indent=1), encoding="utf-8")

async def guard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user: return
    if update.effective_user.id != OWNER_ID:
        try: await update.effective_message.reply_text("not authorized.")
        except Exception: pass
        raise ApplicationHandlerStop

async def cmd_start(update, ctx):
    cid = update.effective_chat.id
    save_history(cid, [{"role": "system", "content": SYSTEM_PROMPT}])
    await update.message.reply_text(
        f"Kanha online.\nmodel: {MODEL}\nbackend: {API_BASE}\n"
        f"/reset  /memory  /temp <n>  /ping")

async def cmd_reset(update, ctx):
    cid = update.effective_chat.id
    save_history(cid, [{"role": "system", "content": SYSTEM_PROMPT}])
    await update.message.reply_text("memory wiped.")

async def cmd_memory(update, ctx):
    cid = update.effective_chat.id
    hist = load_history(cid)
    tail = [m for m in hist[1:] if m.get("role") in ("user","assistant")][-8:]
    text = "\n\n".join(f"[{m['role']}] {str(m.get('content',''))[:200]}" for m in tail)
    await update.message.reply_text(text or "(empty)")

async def cmd_temp(update, ctx):
    if not ctx.args:
        await update.message.reply_text(f"temp = {ctx.chat_data.get('temperature', 0.8)}")
        return
    try:
        ctx.chat_data["temperature"] = float(ctx.args[0])
        await update.message.reply_text(f"temp = {ctx.chat_data['temperature']}")
    except ValueError:
        await update.message.reply_text("not a number.")

async def cmd_ping(update, ctx):
    await update.message.reply_text("up.")

async def on_message(update, ctx):
    text = update.message.text or ""
    if not text.strip(): return
    cid = update.effective_chat.id
    hist = load_history(cid)
    hist.append({"role": "user", "content": text})
    await ctx.bot.send_chat_action(cid, "typing")
    try:
        reply, updated = await run_agent(hist, temperature=ctx.chat_data.get("temperature", 0.8))
    except Exception as e:
        await update.message.reply_text(f"[agent error] {e}"); return
    save_history(cid, updated)
    for i in range(0, len(reply), 4000):
        await update.message.reply_text(reply[i:i+4000])

def main():
    if OWNER_ID == 0:
        raise SystemExit("set OWNER_ID in .env - get your id from @userinfobot on Telegram")
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(TypeHandler(Update, guard), group=-1)
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("reset",  cmd_reset))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("temp",   cmd_temp))
    app.add_handler(CommandHandler("ping",   cmd_ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print(f"bot up - model={MODEL} backend={API_BASE} owner={OWNER_ID}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

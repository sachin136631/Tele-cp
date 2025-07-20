import logging
import httpx
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()  # Load from .env

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("FASTAPI_API_URL", "http://localhost:8000")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        f"👋 heehee, {user.first_name}!\n\n"
        "To report a bug, use:\n"
        "`/report Your bug description here`"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    description = " ".join(context.args)

    if not description:
        await update.message.reply_text(
            "⚠️ Please provide a bug description.\nUsage: `/report something is broken`",
            parse_mode='Markdown'
        )
        return

    bug_payload = {
        "user_telegram_id": str(user.id),  # ✅ Fix: convert to string
        "username": user.username or "",
        "description": description
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(f"{API_URL}/enqueue-bug", json=bug_payload)
            res.raise_for_status()
            data = res.json()
            await update.message.reply_text(f"✅ Bug reported! bro")
        except httpx.HTTPStatusError as e:
            await update.message.reply_text(f"❌ Server error: {e.response.text}")
        except Exception as e:
            await update.message.reply_text(f"❌ Unexpected error: {e}")

async def list_bugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{API_URL}/user-bugs/{user.id}")
            res.raise_for_status()
            bugs = res.json()

            if not bugs:
                await update.message.reply_text("📭 You haven’t reported any bugs yet.")
                return

            msg = "🐞 *Your Bug Reports:*\n\n"
            for bug in bugs[:5]:  # Show only latest 5
                msg += f"🆔 `{bug['id']}`\n📄 {bug['description']}\n📌 *Status:* {bug['status']}\n🕒 {bug['created_at']}\n\n"

            await update.message.reply_text(msg, parse_mode="Markdown")
        except httpx.HTTPStatusError as e:
            await update.message.reply_text(f"❌ Server error: {e.response.text}")
        except Exception as e:
            await update.message.reply_text(f"❌ Unexpected error: {e}")


async def update_bug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Usage: `/update <bug_id> <status>`", parse_mode='Markdown')
        return

    bug_id, status = context.args
    try:
        bug_id = int(bug_id)
    except ValueError:
        await update.message.reply_text("❌ Bug ID should be a number.")
        return

    async with httpx.AsyncClient() as client:
        try:
            res = await client.put(f"{API_URL}/bug/{bug_id}", params={"status": status})
            res.raise_for_status()
            await update.message.reply_text(f"✅ Bug {bug_id} updated to `{status}`", parse_mode="Markdown")
        except httpx.HTTPStatusError as e:
            await update.message.reply_text(f"❌ Server error: {e.response.text}")
        except Exception as e:
            await update.message.reply_text(f"❌ Unexpected error: {e}")

async def delete_bug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /delete <bug_id>")
        return

    bug_id = context.args[0]
    if not bug_id.isdigit():
        await update.message.reply_text("❌ Bug ID must be a number.")
        return

    async with httpx.AsyncClient() as client:
        try:
            res = await client.delete(f"{API_URL}/delete-bug/{bug_id}")
            res.raise_for_status()
            await update.message.reply_text(f"🗑️ Bug {bug_id} deleted successfully.")
        except httpx.HTTPStatusError as e:
            await update.message.reply_text(f"❌ Server error: {e.response.text}")
        except Exception as e:
            await update.message.reply_text(f"❌ Unexpected error: {e}")


def main():
    if not BOT_TOKEN:
        raise Exception("TELEGRAM_BOT_TOKEN not set in environment")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("list", list_bugs))
    app.add_handler(CommandHandler("update", update_bug)) 
    app.add_handler(CommandHandler("delete", delete_bug_cmd))

    print("🚀 Telegram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

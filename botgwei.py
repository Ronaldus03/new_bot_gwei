import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

if not BOT_TOKEN or not ETHERSCAN_API_KEY:
    raise RuntimeError("BOT_TOKEN atau ETHERSCAN_API_KEY belum diset")

GAS_API = (
    "https://api.etherscan.io/v2/api"
    "?chainid=1"
    "&module=gastracker"
    "&action=gasoracle"
    f"&apikey={ETHERSCAN_API_KEY}"
)
# =========================================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⛽ ETH Gas Monitor Bot\n\n"
        "Perintah:\n"
        "/gasstart - mulai update gas\n"
        "/gasstop - hentikan update"
    )


async def gas_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    try:
        r = requests.get(GAS_API, timeout=10)
        data = r.json()

        if data.get("status") != "1":
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ API Error:\n{data.get('result')}"
            )
            return

        gas = data["result"]
        avg_gas_raw = gas["ProposeGasPrice"]      # contoh: "153"
        avg_gas = float(gas["ProposeGasPrice"]) # 0.153

        msg = f"<b>{avg_gas:.3f} gwei</b>"



        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="HTML"
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Error:\n{e}"
        )



async def gasstart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    for job in context.job_queue.get_jobs_by_name(str(chat_id)):
        job.schedule_removal()

    context.job_queue.run_repeating(
        gas_job,
        interval=15,   # update tiap 10 detik
        first=1,
        chat_id=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text("✅ Gas monitor DIMULAI")


async def gasstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))

    if not jobs:
        await update.message.reply_text("❌ Tidak ada job aktif")
        return

    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("🛑 Gas monitor DIHENTIKAN")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasstart", gasstart))
    app.add_handler(CommandHandler("gasstop", gasstop))

    print("⛽ Gas bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()

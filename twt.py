# twt.py
import logging
import requests
import datetime
import pytz
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest

# =======================
#   BOT TOKEN (HARDCODED)
# =======================
# NOTE: you asked to put the token in code. This works but is not secure for public repos.
BOT_TOKEN = "8396419012:AAGfRnHBigdi7Ss6oum1NRm2pUR_-dzUbcA"

FNG_API_URL = "https://api.alternative.me/fng/?limit=1"
FNG_IMAGE_URL = "https://alternative.me/crypto/fear-and-greed-index.png"
BTC_PRICE_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

IST = pytz.timezone("Asia/Kolkata")

SCHEDULE_TIME = datetime.time(hour=5, minute=30, second=1, tzinfo=IST)
CHANNEL_ID = -1002376997748

ACTIVE_CHATS = set()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_btc_price():
    try:
        response = requests.get(BTC_PRICE_API_URL, timeout=10)
        response.raise_for_status()
        price = response.json().get("bitcoin", {}).get("usd")
        if price is not None:
            return f"${price:,.2f}"
    except Exception as e:
        logger.error(f"Error fetching BTC price: {e}")
    return "$00000"


def get_fng_data_caption():
    btc_price = get_btc_price()

    try:
        response = requests.get(FNG_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])

        if data:
            fng = data[0]
            message = (
                f"📊 Crypto Fear and Greed Index\n\n"
                f"🧭 Index Value : {fng.get('value')}\n"
                f"😱 Sentiment : {fng.get('value_classification')}\n"
                f"💰 BTC Price : {btc_price}\n\n"
                f"@ThanosCryptoWorld"
            )
            return message

    except Exception as e:
        logger.error(f"Error fetching FNG data: {e}")
        return "❌ Error fetching FNG data."

    return "❌ No FNG data found."


async def daily_fng_broadcast(context: ContextTypes.DEFAULT_TYPE):
    fng_caption = get_fng_data_caption()
    cache_buster_url = FNG_IMAGE_URL + f"?t={int(time.time())}"

    all_broadcast_chats = ACTIVE_CHATS.copy()
    all_broadcast_chats.add(CHANNEL_ID)

    logger.info(f"Starting scheduled broadcast to {len(all_broadcast_chats)} chats.")

    for chat_id in list(all_broadcast_chats):
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=cache_buster_url,
                caption=fng_caption,
            )
            logger.info(f"Successfully sent FNG to chat {chat_id}.")
        except BadRequest as e:
            # BadRequest often means chat not accessible (bot removed, not admin, etc.)
            logger.warning(f"Error sending to chat {chat_id}: {getattr(e, 'message', e)}. Removing chat if present.")
            if chat_id in ACTIVE_CHATS:
                ACTIVE_CHATS.remove(chat_id)
        except Exception as e:
            logger.error(f"Unexpected error sending to chat {chat_id}: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ACTIVE_CHATS.add(chat_id)

    display_time = SCHEDULE_TIME.strftime("%I:%M:%S %p %Z")

    await update.message.reply_text(
        "👋 FNG Bot activated!\n\n"
        f"This bot will send the Crypto Fear & Greed Index daily at {display_time}.\n"
        "Use /fng to get the data now."
    )


async def fng_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ACTIVE_CHATS.add(chat_id)

    fng_message = get_fng_data_caption()
    cache_buster_url = FNG_IMAGE_URL + f"?t={int(time.time())}"

    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=cache_buster_url,
            caption=fng_message,
        )
    except Exception as e:
        logger.error(f"Failed to send FNG message to {chat_id}: {e}")


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # schedule daily broadcast (will use bot's timezone handling)
    application.job_queue.run_daily(
        daily_fng_broadcast,
        time=SCHEDULE_TIME,
        days=(0, 1, 2, 3, 4, 5, 6),
        name="daily_fng_broadcast",
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("fng", fng_command))

    logger.info("Bot started and running… (polling mode)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

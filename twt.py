import logging
import requests
import datetime
import pytz
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TimedOut, BadRequest

BOT_TOKEN = "8396419012:AAGfRnHBigdi7Ss6oum1NRm2pUR_-dzUbcA" 

FNG_API_URL = "https://api.alternative.me/fng/?limit=1" 
FNG_IMAGE_URL = "https://alternative.me/crypto/fear-and-greed-index.png"
BTC_PRICE_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

IST = pytz.timezone('Asia/Kolkata')

SCHEDULE_TIME = datetime.time(hour=5, minute=30, second=1, tzinfo=IST)
CHANNEL_ID = -1002376997748

ACTIVE_CHATS = set()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(name)


def get_btc_price():
    try:
        response = requests.get(BTC_PRICE_API_URL)
        response.raise_for_status()
        price = response.json().get('bitcoin', {}).get('usd')
        if price:
            return f"${price:,.2f}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching BTC price: {e}")
    return "$00000"

def get_fng_data_caption():
    btc_price = get_btc_price()
    
    try:
        response = requests.get(FNG_API_URL)
        response.raise_for_status()
        data = response.json().get('data', [])
        if data:
            fng = data[0]
            
           
            message = (
                f"📊 Crypto Fear and Greed Index\n\n"
                f"🧭 Index Value : {fng.get('value')}\n"
                f"😱 Sentiment : {fng.get('value_classification')}\n"
                f"💰 BTC Price : {btc_price}\n\n"
                f" @ThanosCryptoWorld"
            )
            return message
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching FNG data: {e}")
        return "❌ Error fetching FNG data."
    except Exception as e:
        logger.error(f"Error processing FNG data: {e}")
        return "❌ Error processing FNG data."



async def daily_fng_broadcast(context: ContextTypes.DEFAULT_TYPE) -> None:
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
                parse_mode=None 
            )
            logger.info(f"Successfully sent FNG to chat {chat_id}.")
        except BadRequest as e:
            logger.warning(f"Error sending to chat {chat_id}: {e.message}. Removing chat.")
            if chat_id in ACTIVE_CHATS:
                ACTIVE_CHATS.remove(chat_id)
        except Exception as e:
            logger.error(f"Failed to send to chat {chat_id} due to unexpected error: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ACTIVE_CHATS.add(chat_id)
    
    display_time = SCHEDULE_TIME.strftime('%I:%M:%S %p %Z')
    
    await update.message.reply_text(
        "👋 FNG Bot activated!\n\n"
        f"This bot is scheduled to send the Crypto Fear & Greed Index image daily at {display_time} to this chat.\n"
        "Use /fng to get the index image and details immediately."
    )

async def fng_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ACTIVE_CHATS.add(chat_id)

    fng_message = get_fng_data_caption()
    
    cache_buster_url = FNG_IMAGE_URL + f"?t={int(time.time())}"
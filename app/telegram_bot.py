import logging
import telegram
import os


logging.basicConfig(level=logging.INFO,
                    filemode='a',
                    encoding='utf-8',
                    format='{asctime}: {message}',
                    style='{',
                    datefmt="%Y-%m-%d %H:%M")

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_id = os.environ.get('TELEGRAM_BOT_CHAT_ID')

async def telegram_bot_send_message(message):
    bot = telegram.Bot(BOT_TOKEN)
    async with bot:
        await bot.send_message(text=message, chat_id=chat_id, parse_mode='HTML')

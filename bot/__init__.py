from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN
from bot.handlers import dp
from bot.setup import set_default_commands, set_webhook


bot = Bot(token=str(BOT_TOKEN), default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))
dispatcher = dp

async def init_bot():
    await set_webhook(bot)
    await set_default_commands(bot)

async def handle_webhook_update(update: types.Update):
    return await dp.feed_webhook_update(bot, update)
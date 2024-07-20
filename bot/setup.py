from aiogram import Bot, types

from bot.config import WEBHOOK_SECRET, WEBHOOK_URL, WEBHOOK_PATH

# Set bot commands
def get_commands_en():
    commands = [
        types.BotCommand(command="/start", description="Start the bot"),
        types.BotCommand(command="/help", description="Help"),
    ]
    return commands


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(get_commands_en(), scope=types.BotCommandScopeAllPrivateChats(), language_code="en")

async def set_webhook(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH, secret_token=WEBHOOK_SECRET)
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from md2tgmd import escape
import re

from utils.scraper import scrape
from bot.helpers import fetch_all_products, add_new_product, fetch_one_product, delete_one
from utils.regex_patterns import amazon_url_patterns, all_url_patterns

logger = logging.getLogger(__name__)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    text = (
        f"Hello {message.chat.username}! 🌟\n\n"
        "I'm PriceTrackerBot, your personal assistant for tracking product prices. 💸\n\n"
        "To get started, use the /my_trackings command to start tracking a product. "
        "Simply send the url:\n"
        "For example:\n"
        "I'll keep you updated on any price changes for the products you're tracking. "
        "Feel free to ask for help with the /help command at any time. Happy tracking! 🚀"
    )

    await message.reply(escape(text), quote=True)


@dp.message(Command("help"))
async def help(message: Message):
    text = (
        "🤖 **Price Tracker Bot Help**\n\n"
        "Here are the available commands:\n"
        "1. `/my_trackings`: View all the products you are currently tracking.\n"
        "2. `/stop < product_id >`: Stop tracking a specific product. Replace `<product_id>` with the product ID you want to stop tracking.\n"
        "3. `/product < product_id >`: Get detailed information about a specific product. Replace `<product_id>` with the product ID you want information about.\n"
        "\n\n**How It Works:**\n\n"
        "1. Send the product link from Flipkart.\n"
        "2. The bot will automatically scrape and track the product.\n"
        "3. If there is a price change, the bot will notify you with the updated information.\n"
        "Feel free to use the commands and start tracking your favorite products!\n"
    )
    await message.reply(escape(text), quote=True)


@dp.message(Command("my_trackings"))
async def track(message: Message):
    try:
        chat_id = message.chat.id
        text = await message.reply(escape("Fetching Your Products..."))
        products = await fetch_all_products(chat_id)
        if products:
            products_message = "Your Tracked Products:\n\n"

            for i, product in enumerate(products, start=1):
                _id = product.get("product_id")
                product_name = product.get("product_name")
                product_url = product.get("url")
                product_price = product.get("price")

                products_message += f"🏷️ **Product {i}**: [{product_name}]({product_url})\n\n"
                products_message += f"💰 **Current Price**: {product_price}\n"
                products_message += f"❌ Use `/stop {_id}` to Stop tracking\n\n"

            await text.edit_text(escape(products_message), disable_web_page_preview=True)
        else:
            await text.edit_text("No products added yet")
    except Exception as e:
        logger.error(e, exc_info=True)


@dp.message(F.text.regexp("|".join(all_url_patterns)))
async def track_flipkart_url(message: Message):
    try:
        url = message.text or ""
        platform = "amazon" if any(re.match(pattern, url) for pattern in amazon_url_patterns) else "flipkart"
        product_name, price = await scrape(url, platform)
        status = await message.reply(escape("Adding Your Product... Please Wait!!"))
        if product_name and price:
            id = await add_new_product(
                message.chat.id, product_name, message.text, price
            )
            await status.edit_text(escape(
                f'Tracking your product "{product_name}"!\n\n'
                f"You can use\n `/product {id}` to get more information about it."
            ))
        else:
            await status.edit_text(escape("Failed to scrape !!!"))
    except Exception as e:
        logger.error(e, exc_info=True)


@dp.message(Command("product"))
async def track_product(message: Message):
    try:
        if message.text:
            __, id = message.text.split()
            status = await message.reply(escape("Getting Product Info...."))
            if id:
                product = await fetch_one_product(id)
                if product:
                    product_name = product.get("product_name")
                    product_url = product.get("url")
                    product_price = product.get("price")
                    maximum_price = product.get("upper")
                    minimum_price = product.get("lower")

                    products_message = (
                        f"🛍 **Product:** [{product_name}]({product_url})\n\n"
                        f"💲 **Current Price:** {product_price}\n"
                        f"📉 **Lowest Price:** {minimum_price}\n"
                        f"📈 **Highest Price:** {maximum_price}\n"
                        f"\n\n\nTo Stop Tracking, use `/stop {id}`"
                    )

                    await status.edit_text(escape(products_message), disable_web_page_preview=True)
                else:
                    await status.edit_text("Product Not Found")
            else:
                await status.edit_text("Failed to fetch the product")
    except Exception as e:
        logger.error(e, exc_info=True)


@dp.message(Command("stop"))
async def delete_product(message: Message):
    try:
        if message.text:
            __, id = message.text.split()
            status = await message.reply(escape("Deleting Product...."))
            chat_id = message.chat.id
            if id:
                is_deleted = await delete_one(id, chat_id)
                if is_deleted:
                    await status.edit_text("Product Deleted from Your Tracking List")
                else:
                    await status.edit_text("Failed to Delete the product")
            else:
                await status.edit_text("Failed to Delete the product")
    except Exception as e:
        logger.error(e, exc_info=True)


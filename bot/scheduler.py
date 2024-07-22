import asyncio
import logging
import re
import time
from utils.scraper import scrape
from fastapi import Request, Response

from bot import bot
from utils.regex_patterns import amazon_url_patterns
from utils.db import all_products, update_product_price, track_by_product, Product

logger = logging.getLogger(__name__)


async def check_prices(_: Request):
    updated_products: list[Product] = []

    logger.info("Checking Price for Products...")
    for product in await all_products():
        platform = "amazon" if any(re.match(pattern, product.url) for pattern in amazon_url_patterns) else "flipkart"
        __, current_price = await scrape(product.url, platform)
        await asyncio.sleep(1)
        if current_price is not None:
            if current_price != product.price and (updated_product := await update_product_price(product.id, float(current_price))):
                updated_products.append(updated_product)
    logger.info("Completed")
    
    changed_products = await compare_prices(updated_products)
    for changed_product in changed_products:
        trackers = await track_by_product(changed_product.id)
        for tracker in trackers:
            if product:= tracker.product:
                percentage_change = (
                    (product.price - product.previous_price)
                    / product.previous_price
                ) * 100
                text = (
                    f"🎉 Good news! The price of {product.product_name} has changed.\n"
                    f"   - Previous Price: ₹{product.previous_price:.2f}\n"
                    f"   - Current Price: ₹{product.price:.2f}\n"
                    f"   - Percentage Change: {percentage_change:.2f}%\n"
                    f"   - [Check it out here]({product.url})"
                )
                await bot.send_message(
                    chat_id=tracker.user_id,
                    text=text,
                    disable_web_page_preview=True
                )

    return Response(status_code=200)


async def compare_prices(products: list[Product] = []):
    logger.info("Comparing Prices...")
    product_with_changes: list[Product] = []
    for product in products:
        current_price = product.price
        previous_price = product.previous_price
        if current_price != previous_price:
            product_with_changes.append(product)

    return product_with_changes

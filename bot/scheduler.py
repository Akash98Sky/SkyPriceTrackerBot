import logging
import re
import time
from pymongo import MongoClient
import os
from utils.scraper import scrape
from fastapi import Request, Response

from bot import bot
from utils.regex_patterns import amazon_url_patterns


dbclient = MongoClient(os.getenv("MONGO_URI"))
database = dbclient[os.getenv("DATABASE", "PriceTrackerBot")]
collection = database[os.getenv("COLLECTION", "PriceTracker")]
PRODUCTS = database[os.getenv("PRODUCTS", "PriceTrackerGlobal")]

logger = logging.getLogger(__name__)


async def check_prices(_: Request):
    logger.info("Checking Price for Products...")
    for product in PRODUCTS.find():
        platform = "amazon" if any(re.match(pattern, product["url"]) for pattern in amazon_url_patterns) else "flipkart"
        __, current_price = await scrape(product["url"], platform)
        time.sleep(1)
        if current_price is not None:
            if current_price != product["price"]:
                PRODUCTS.update_one(
                    {"_id": product["_id"]},
                    {
                        "$set": {
                            "price": current_price,
                            "previous_price": product["price"],
                            "lower": current_price
                            if current_price < product["lower"]
                            else product["lower"],
                            "upper": current_price
                            if current_price > product["upper"]
                            else product["upper"],
                        }
                    },
                )
    logger.info("Completed")
    changed_products = await compare_prices()
    for changed_product in changed_products:
        cursor = collection.find({"product_id": changed_product})
        users = list(cursor)
        for user in users:
            product = PRODUCTS.find_one({"_id": user.get("product_id")})
            if product:
                percentage_change = (
                    (product["price"] - product["previous_price"])
                    / product["previous_price"]
                ) * 100
                text = (
                    f"🎉 Good news! The price of {product['product_name']} has changed.\n"
                    f"   - Previous Price: ₹{product['previous_price']:.2f}\n"
                    f"   - Current Price: ₹{product['price']:.2f}\n"
                    f"   - Percentage Change: {percentage_change:.2f}%\n"
                    f"   - [Check it out here]({product['url']})"
                )
                await bot.send_message(
                    chat_id=user.get("user_id"), text=text, disable_web_page_preview=True
                )

    return Response(status_code=200)


async def compare_prices():
    logger.info("Comparing Prices...")
    product_with_changes = []
    for product in PRODUCTS.find():
        current_price = product.get("price")
        previous_price = product.get("previous_price")
        if current_price != previous_price:
            product_with_changes.append(product.get("_id"))

    return product_with_changes

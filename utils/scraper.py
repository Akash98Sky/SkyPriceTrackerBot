import logging
from asyncio import TimeoutError

from utils.scrapers.flipkart import ExtractFlipkart
from utils.scrapers.amazon import ExtractAmazon
from utils.scrapers.generic import ExtractGeneric

logger = logging.getLogger(__name__)

async def scrape(url: str, platform: str):
    try:
        title, price = None, None
        if platform == "flipkart":
            async with ExtractFlipkart(url) as product:
                title = product.get_title()
                price = product.get_price()
        elif platform == "amazon":
            async with ExtractAmazon(url) as product:
                title = product.get_title()
                price = product.get_price()

        if title and price:
            return title, price
        else:
            async with ExtractGeneric(url) as product:
                return product.get_title(), product.get_price()

    except TimeoutError:
        async with ExtractGeneric(url) as product:
            return product.get_title(), product.get_price()
    except Exception as e:
        logger.error(e, exc_info=True)
        return None, None

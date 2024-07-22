import logging

from utils.scrapers.flipkart import ExtractFlipkart
from utils.scrapers.amazon import ExtractAmazon

logger = logging.getLogger(__name__)

async def scrape(url: str, platform: str):
    try:
        if platform == "flipkart":
            async with ExtractFlipkart(url) as product:
                return product.get_title(), product.get_price()
        elif platform == "amazon":
            async with ExtractAmazon(url) as product:
                return product.get_title(), product.get_price()
        else:
            raise ValueError("Unsupported platform")

    except Exception as e:
        logger.error(e, exc_info=True)
        return None, None

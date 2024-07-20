import logging
from typing import Union
from python_flipkart_scraper import ExtractFlipkart
from python_amazon_scraper import ExtractAmazon

logger = logging.getLogger(__name__)

async def scrape(url: str, platform: str):
    try:
        if platform == "flipkart":
            product = ExtractFlipkart(url)
        elif platform == "amazon":
            product = ExtractAmazon(url)
        else:
            raise ValueError("Unsupported platform")

        price = str(product.get_price())
        product_name = str(product.get_title())
        return product_name, price
    except Exception as e:
        logger.error(e, exc_info=True)
        return None, None

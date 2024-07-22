import logging
from prisma.client import Prisma
from prisma.models import Product, PriceTracker
from prisma.types import ProductCreateInput

logger = logging.getLogger(__name__)

db_client = Prisma()

price_trackers = db_client.pricetracker
products = db_client.product

async def track_by_user(user_id: int) -> list[PriceTracker]:
    try:
        return await price_trackers.find_many(where={ "user_id": user_id }, include={ "product": True })

    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return []

async def track_by_product(product_id: str) -> list[PriceTracker]:
    try:
        return await price_trackers.find_many(where={ "product_id": product_id }, include={ "product": True })

    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return []

async def get_tracker(tracker_id: str):
    try:
        if tracker := await price_trackers.find_unique(where={ "id": tracker_id }, include={ "product": True }):
            return tracker.product

    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return None


async def add_tracker(user_id: int, product_name: str, product_url: str, initial_price: float):
    try:
        existing_product = await products.find_first(where={ "product_name": product_name })
        if not existing_product:
            new_product = ProductCreateInput({
                "product_name": product_name,
                "url": product_url,
                "price": initial_price,
                "previous_price": initial_price,
                "upper": initial_price,
                "lower": initial_price,
            })
            existing_product = await products.create(data=new_product)

        tracker = await price_trackers.find_first(
            where={ "user_id": user_id, "product_id": existing_product.id }
        )

        if tracker:
            logger.info("Product already exists.")
            return tracker

        tracker = await price_trackers.create({
            "user_id": user_id,
            "product_id": existing_product.id,
        })

        logger.info("Product added successfully.")
        return tracker

    except Exception as e:
        logger.error(f"Error adding product: {str(e)}", exc_info=True)
        return None


async def update_product_price(id: str, new_price: float):
    try:
        product = await products.find_unique(
            { "id": id },
        )

        if product:
            upper_price = product.upper
            lower_price = product.lower

            if new_price > upper_price:
                upper_price = new_price
            elif new_price < lower_price:
                lower_price = new_price

            updated_product = await products.update(
                {
                    "previous_price": product.price,
                    "price": new_price,
                    "upper": upper_price,
                    "lower": lower_price,
                },
                where={ "id": id }
            )
            logger.info("Global product prices updated successfully.")
            return updated_product
    except Exception as e:
        logger.error(f"Error updating product price: {str(e)}")


async def delete_tracker(id: str, user_id: int):
    try:
        if tracker := await price_trackers.find_first(where={ "id": id, "user_id": user_id }):
            await price_trackers.delete({ "id": tracker.id })
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        return False
  
async def all_products(include_trackers: bool = False) -> list[Product]:
    try:
        return await products.find_many(include={ "price_trackers": include_trackers }, order={ "updated_at": "asc" })
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        return []

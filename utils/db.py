import json
import logging
import os
from prisma.client import Prisma
from prisma.models import Product, PriceTracker
from prisma.types import ProductCreateInput
from bson.objectid import ObjectId
from deta import Deta
from datetime import datetime
import pytz

DETA_APP = True if os.getenv("DETA_SPACE_APP", True) else False
logger = logging.getLogger(__name__)
timezone = pytz.timezone("Asia/Kolkata")

if DETA_APP:
    deta_db = Deta()
    price_trackers_base = deta_db.AsyncBase("price_trackers")
    products_base = deta_db.AsyncBase("products")
else:
    prisma_db = Prisma()
    price_trackers = prisma_db.pricetracker
    products = prisma_db.product


async def connect():
    if not DETA_APP:
        await prisma_db.connect()

async def disconnect():
    if not DETA_APP:
        await prisma_db.disconnect()

async def __base_track_by_user(user_id: int) -> list[PriceTracker]:
    try:
        res = await price_trackers_base.fetch({ "user_id": user_id })
        for tracker in res.items:
            if product_data := await products_base.get(tracker["product_id"]):
                tracker["product"] = Product(**product_data)
        return [PriceTracker(**tracker) for tracker in res.items]

    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        return []

async def __prisma_track_by_user(user_id: int) -> list[PriceTracker]:
    try:
        return await price_trackers.find_many(where={ "user_id": user_id }, include={ "product": True })

    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return []

async def __base_track_by_product(product_id: str) -> list[PriceTracker]:
    try:
        res = await price_trackers_base.fetch({ "product_id": product_id })
        for tracker in res.items:
            if product_data := await products_base.get(tracker["product_id"]):
                tracker["product"] = Product(**product_data)
        return [PriceTracker(**tracker) for tracker in res.items]

    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return []
    
async def __prisma_track_by_product(product_id: str) -> list[PriceTracker]:
    try:
        return await price_trackers.find_many(where={ "product_id": product_id }, include={ "product": True })

    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return []

async def __base_get_tracker(tracker_id: str):
    try:
        if tracker := await price_trackers_base.get(tracker_id):
            if product_data := await products_base.get(tracker["product_id"]):
                tracker["product"] = Product(**product_data)
            return PriceTracker(**tracker)

    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return None

async def __prisma_get_tracker(tracker_id: str):
    try:
        if tracker := await price_trackers.find_unique(where={ "id": tracker_id }, include={ "product": True }):
            return tracker

    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return None

async def __base_add_tracker(user_id: int, product_name: str, product_url: str, initial_price: float):
    try:
        res = await products_base.fetch({ "product_name": product_name })
        if res.count == 0:
            key = str(ObjectId())
            existing_product = Product(**{
                "id": key,
                "product_name": product_name,
                "url": product_url,
                "price": initial_price,
                "previous_price": initial_price,
                "upper": initial_price,
                "lower": initial_price,
                "updated_at": datetime.now(timezone)
            })
            await products_base.put(json.loads(existing_product.model_dump_json()), key)
        else:
            existing_product = Product(**res.items[0])

        tracker_res = await price_trackers_base.fetch({ "user_id": user_id, "product_id": existing_product.id })
        if tracker_res.count > 0:
            logger.info("Product already exists.")
            return PriceTracker(**tracker_res.items[0])
        
        key = str(ObjectId())
        tracker = await price_trackers_base.put(PriceTracker(**{
            "id": key,
            "user_id": user_id,
            "product_id": existing_product.id
        }).model_dump(), key)

        if tracker:
            logger.info("Product added successfully.")
            return PriceTracker(**tracker)

    except Exception as e:
        logger.error(f"Error adding product: {str(e)}", exc_info=True)
        return None

async def __prisma_add_tracker(user_id: int, product_name: str, product_url: str, initial_price: float):
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


async def __base_update_product_price(id: str, new_price: float):
    try:
        product_data = await products_base.get(id)
        if product_data and (product := Product(**product_data)):
            upper_price = product.upper
            lower_price = product.lower

            if new_price > upper_price:
                upper_price = new_price
            elif new_price < lower_price:
                lower_price = new_price

            updated_product = Product(**product_data)

            updated_product.previous_price = product.price
            updated_product.price = new_price
            updated_product.upper = upper_price
            updated_product.lower = lower_price
            updated_product.updated_at = datetime.now(timezone)

            await products_base.update(json.loads(updated_product.model_dump_json()), key=id)

            logger.info("Global product prices updated successfully.")
            return updated_product
    except Exception as e:
        logger.error(f"Error updating product price: {str(e)}")

async def __prisma_update_product_price(id: str, new_price: float):
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


async def __base_delete_tracker(id: str, user_id: int):
    try:
        if tracker_data := await price_trackers_base.get(id):
            tracker = PriceTracker(**tracker_data)
            if tracker.user_id == user_id:
                await price_trackers_base.delete(id)
                return True
            else:
                return False
        else:
            return False

    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        return False

async def __prisma_delete_tracker(id: str, user_id: int):
    try:
        if tracker := await price_trackers.find_first(where={ "id": id, "user_id": user_id }):
            await price_trackers.delete({ "id": tracker.id })
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        return False
    

async def __base_all_products(include_trackers: bool = False) -> list[Product]:
    try:
        products_res = await products_base.fetch()
        products: list[Product] = []

        for product in products_res.items:
            product = Product(**product)
            if include_trackers:
                product.price_trackers = []
                trackers_res = await price_trackers_base.fetch({ "product_id": product.id })
                for tracker in trackers_res.items:
                    product.price_trackers.append(PriceTracker(**tracker))
            products.append(product)

        return products

    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        return []
  
async def __prisma_all_products(include_trackers: bool = False) -> list[Product]:
    try:
        return await products.find_many(include={ "price_trackers": include_trackers }, order={ "updated_at": "asc" })
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        return []

track_by_user = __base_track_by_user if DETA_APP else __prisma_track_by_user
track_by_product = __base_track_by_product if DETA_APP else __prisma_track_by_product
get_tracker = __base_get_tracker if DETA_APP else __prisma_get_tracker
add_tracker = __base_add_tracker if DETA_APP else __prisma_add_tracker
update_product_price = __base_update_product_price if DETA_APP else __prisma_update_product_price
delete_tracker = __base_delete_tracker if DETA_APP else __prisma_delete_tracker
all_products = __base_all_products if DETA_APP else __prisma_all_products
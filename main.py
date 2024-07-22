import logging
from aiogram import types
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
import os
import uvicorn

from bot import handle_webhook_update, init_bot
from bot.scheduler import check_prices
from bot.config import WEBHOOK_SECRET, WEBHOOK_PATH
from models import ActionBody
from utils.db import db_client

load_dotenv()


WEB_SERVER_HOST = os.getenv("HOST", "0.0.0.0")
WEB_SERVER_PORT = os.getenv("PORT", "8080")
logger = logging.getLogger(__name__)


app = FastAPI()

@app.get('/setup')
async def setup(drop_pending: bool = False):
    await init_bot(drop_pending)
    logger.info("Bot has been initialized...")
    return Response(status_code=200, content="Bot has been initialized...")

@app.post(WEBHOOK_PATH)
async def handle_webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

    if secret == WEBHOOK_SECRET:
        try:
            update = types.Update(**await request.json())
            await handle_webhook_update(update)
            return Response()
        
        except Exception as e:
            logger.error(e, exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error: " + str(e))
    else:
        raise HTTPException(status_code=403, detail="Forbidden: Wrong secret token")

    
@app.post("/__space/v0/actions")
async def handle_actions(action: ActionBody, request: Request):
    event = action.event

    if (event.id == "scheduled_price_check"):
        return await check_prices(request)

    raise HTTPException(status_code=404, detail="Action not found")

async def on_startup():
    await db_client.connect()

async def on_shutdown():
    await db_client.disconnect()

app.add_event_handler("startup", on_startup)
app.add_event_handler("shutdown", on_shutdown)


if __name__ == "__main__":
    uvicorn.run(app, host=WEB_SERVER_HOST, port=int(WEB_SERVER_PORT))

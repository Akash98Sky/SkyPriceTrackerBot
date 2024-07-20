
import os
from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_PATH = "/tg_bot"

# If the app is running in deta space
if os.getenv("DETA_SPACE_APP"):
    WEBHOOK_URL = f"https://{os.getenv('DETA_SPACE_APP_HOSTNAME')}"


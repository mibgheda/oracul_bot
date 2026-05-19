import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
ADMIN_ID: int = int(os.environ["ADMIN_ID"])
PRIVACY_POLICY_URL: str = os.environ.get("PRIVACY_POLICY_URL", "https://example.com/privacy")
DB_PATH: str = os.environ.get("DB_PATH", "oracul.db")

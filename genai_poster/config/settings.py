import logging
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

LOG = logging.getLogger("festival_linkedin_bot")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

INDIA_TZ = ZoneInfo("Asia/Kolkata")

DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_IMAGE_MODEL = os.getenv("IMAGE_MODEL", "dall-e-3")
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./downloads")).resolve()
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

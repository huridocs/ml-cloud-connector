import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

INSTANCE_ID = os.getenv("INSTANCE_ID")
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION")
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
CONSUMER_KEY = os.getenv("CONSUMER_KEY")

PUB_KEY_PATH = Path(ROOT_DIR, "ovh.pub")

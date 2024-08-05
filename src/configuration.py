import os

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

INSTANCE_ID = os.getenv("INSTANCE_ID")
PROJECT_ID = os.getenv("PROJECT_ID")

if __name__ == '__main__':
    print(INSTANCE_ID)
    print(PROJECT_ID)
    print(ROOT_DIR)
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Root level configuration for project
    """

    URL = os.getenv("URL")

    KEY = os.getenv("KEY")

    REDIS_URL = os.getenv("LOCAL_REDIS_INSTANCE")

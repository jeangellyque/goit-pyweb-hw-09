import os
from pathlib import Path

from dotenv import load_dotenv
from redis import Redis


def create_cache_client():
    credentials_file = Path(__file__).resolve().with_name("atlas-credentials.env")
    load_dotenv(credentials_file)
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = Redis.from_url(redis_url, decode_responses=True)
    client.ping()
    return client

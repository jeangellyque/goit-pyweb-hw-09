import os
from pathlib import Path

from dotenv import load_dotenv
from mongoengine import connect


def connect_to_database():
    credentials_file = Path(__file__).resolve().with_name("atlas-credentials.env")
    load_dotenv(credentials_file)

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            f"MONGODB_URI is missing from the environment or {credentials_file}"
        )

    return connect(db="quotes_db", host=uri)

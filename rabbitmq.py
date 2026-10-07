import os
from pathlib import Path

import pika
from dotenv import load_dotenv


EMAIL_QUEUE_NAME = "email_contacts"
SMS_QUEUE_NAME = "sms_contacts"
QUEUE_NAME = EMAIL_QUEUE_NAME
DEFAULT_RABBITMQ_USER = "mailer"
DEFAULT_RABBITMQ_PASSWORD = "local_mailer_password"


def create_rabbitmq_connection():
    project_env = Path(__file__).resolve().with_name(".env")
    load_dotenv(project_env)

    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", DEFAULT_RABBITMQ_USER),
        os.getenv("RABBITMQ_PASSWORD", DEFAULT_RABBITMQ_PASSWORD),
    )
    parameters = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
    )
    return pika.BlockingConnection(parameters)

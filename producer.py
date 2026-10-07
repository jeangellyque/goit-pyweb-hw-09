import argparse
import json
import logging

import pika
from faker import Faker

from database import connect_to_database
from models import Contact
from rabbitmq import (
    EMAIL_QUEUE_NAME,
    SMS_QUEUE_NAME,
    create_rabbitmq_connection,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate fake contacts and queue email notifications."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="number of contacts to create (default: 10)",
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be greater than zero")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    connect_to_database()
    fake = Faker()

    with create_rabbitmq_connection() as connection:
        channel = connection.channel()
        channel.queue_declare(queue=EMAIL_QUEUE_NAME, durable=True)
        channel.queue_declare(queue=SMS_QUEUE_NAME, durable=True)
        channel.confirm_delivery()

        for _ in range(args.count):
            contact = Contact(
                fullname=fake.name(),
                email=fake.unique.email(),
                phone_number=fake.phone_number(),
                preferred_channel=fake.random_element(elements=("email", "sms")),
            ).save()
            queue_name = (
                EMAIL_QUEUE_NAME
                if contact.preferred_channel == "email"
                else SMS_QUEUE_NAME
            )
            message = json.dumps({"contact_id": str(contact.id)})
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message.encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
                mandatory=True,
            )
            logging.info(
                "Queued %s contact %s",
                contact.preferred_channel,
                contact.fullname,
            )

    logging.info("Created and queued %d contacts.", args.count)


if __name__ == "__main__":
    main()

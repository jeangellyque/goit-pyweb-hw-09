import json
import logging
from functools import partial

import pika
from bson import ObjectId
from mongoengine.errors import MongoEngineException
from pymongo.errors import PyMongoError

from database import connect_to_database
from models import Contact
from rabbitmq import create_rabbitmq_connection


def send_email_stub(contact):
    logging.info("Simulated email sent to %s <%s>", contact.fullname, contact.email)


def send_sms_stub(contact):
    logging.info(
        "Simulated SMS sent to %s <%s>",
        contact.fullname,
        contact.phone_number,
    )


SEND_STUBS = {"email": send_email_stub, "sms": send_sms_stub}


def process_message(channel, method, properties, body, delivery_method):
    try:
        message = json.loads(body)
        contact_id = message["contact_id"]
        if not isinstance(contact_id, str) or not ObjectId.is_valid(contact_id):
            raise ValueError("contact_id must be a valid ObjectID string")
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError):
        logging.exception("Discarding invalid RabbitMQ message.")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    sent_field = f"{delivery_method}_sent"
    try:
        contact = Contact.objects(id=ObjectId(contact_id)).first()
        if contact is None:
            logging.warning("Contact %s does not exist; discarding message.", contact_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        if contact.preferred_channel != delivery_method:
            logging.error(
                "Contact %s was sent to the wrong channel queue; discarding message.",
                contact_id,
            )
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        if getattr(contact, sent_field):
            logging.info(
                "%s already sent to %s; acknowledging duplicate.",
                delivery_method.upper(),
                contact.email if delivery_method == "email" else contact.phone_number,
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        SEND_STUBS[delivery_method](contact)
        Contact.objects(id=contact.id, **{sent_field: False}).update_one(
            **{f"set__{sent_field}": True}
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except (MongoEngineException, PyMongoError):
        logging.exception("Contact processing failed; message will be requeued.")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def run_consumer(queue_name, delivery_method):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    connect_to_database()
    with create_rabbitmq_connection() as connection:
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=partial(
                process_message,
                delivery_method=delivery_method,
            ),
        )
        logging.info(
            "Waiting for %s contacts in queue %s. Press Ctrl+C to stop.",
            delivery_method,
            queue_name,
        )
        channel.start_consuming()

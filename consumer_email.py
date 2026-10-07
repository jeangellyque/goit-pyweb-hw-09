from consumer_common import run_consumer
from rabbitmq import EMAIL_QUEUE_NAME


def main():
    run_consumer(EMAIL_QUEUE_NAME, "email")


if __name__ == "__main__":
    main()

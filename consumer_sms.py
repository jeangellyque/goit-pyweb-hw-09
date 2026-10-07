from consumer_common import run_consumer
from rabbitmq import SMS_QUEUE_NAME


def main():
    run_consumer(SMS_QUEUE_NAME, "sms")


if __name__ == "__main__":
    main()

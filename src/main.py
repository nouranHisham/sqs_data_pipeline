import time
import json
import boto3
from botocore.exceptions import ClientError
from sqs_client import get_sqs_client, receive_messages, delete_message
from transformer import transform_to_trip
from database_loader import (
    create_database,
    get_db_connection,
    create_table,
    insert_event
)
from config import POLLING_SLEEP_SECONDS

# Wait until queue exists
def wait_for_queue(sqs_client, queue_name, retries=20, delay=3):
    for i in range(retries):
        try:
            response = sqs_client.get_queue_url(QueueName=queue_name)
            print(f"Queue '{queue_name}' found!")
            return response["QueueUrl"]
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                print(f"Queue not ready yet ({i+1}/{retries}), retrying in {delay}s...")
            else:
                raise
        time.sleep(delay)
    raise Exception(f"Queue {queue_name} does not exist after retries")

def main():
    sqs_client = get_sqs_client()

    queue_name = "test-queue"
    SQS_QUEUE_URL = wait_for_queue(sqs_client, queue_name)

    create_database()
    conn = get_db_connection()
    create_table(conn)

    print("Starting ETL consumer...")

    max_idle_time = 30
    idle_time = 0

    while True:
        messages = receive_messages(sqs_client, SQS_QUEUE_URL)

        if not messages:
            print(f"No messages, waiting {POLLING_SLEEP_SECONDS}s...")
            time.sleep(POLLING_SLEEP_SECONDS)
            idle_time += POLLING_SLEEP_SECONDS

            if idle_time >= max_idle_time:
                print("Queue empty for 30 seconds. Exiting.")
                break
            continue

        # Messages received → reset idle timer
        idle_time = 0
        print(f"Received {len(messages)} message(s)")

        for msg in messages:
            receipt_handle = msg["ReceiptHandle"]

            try:
                transformed = transform_to_trip(msg["Body"])
                insert_event(conn, transformed)

                delete_message(
                    sqs_client,
                    SQS_QUEUE_URL,
                    receipt_handle
                )

                print(
                    f"Processed and deleted message "
                    f"(event id={transformed['id']})"
                )

            except json.JSONDecodeError:
                print("Malformed message (invalid JSON). Deleting it.")

                delete_message(
                    sqs_client,
                    SQS_QUEUE_URL,
                    receipt_handle
                )

            except Exception as e:
                print(f"Error processing message: {e}")
                print("Message NOT deleted, will be retried by SQS")


if __name__ == "__main__":
    main()

import boto3
from botocore.config import Config
from config import (
    AWS_REGION,
    AWS_ENDPOINT_URL,
    AWS_ACCESS_KEY,
    AWS_SECRET_KEY,
    SQS_MAX_MESSAGES,
    SQS_WAIT_TIME
)

def get_sqs_client():
    return boto3.client(
        "sqs",
        region_name=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        config=Config(
            retries={"max_attempts": 3},
            signature_version="v4"
        )
    )

def receive_messages(sqs_client, queue_url):
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=SQS_MAX_MESSAGES,
        WaitTimeSeconds=SQS_WAIT_TIME
    )
    return response.get("Messages", [])

def delete_message(sqs_client, queue_url, receipt_handle):
    sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
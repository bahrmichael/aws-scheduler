import boto3

client = boto3.client('sqs')


def publish_sqs(url, payload):
    return client.send_message_batch(
        QueueUrl=url,
        Entries=payload
    )

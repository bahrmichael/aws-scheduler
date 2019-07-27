import boto3

client = boto3.client('sns')


def publish_sns(arn, payload):
    client.publish(
        TopicArn=arn,
        Message=payload
    )

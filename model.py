import os

import boto3

table_name = f'aws-scheduler-events-v2-{os.environ.get("STAGE")}'
table = boto3.resource('dynamodb').Table(table_name)
client = boto3.client('dynamodb')
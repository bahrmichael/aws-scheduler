import json
import os
from datetime import datetime

from boto3.dynamodb.types import TypeDeserializer

from lambda_client import invoke_lambda
from model import client, table_name
from util import make_chunks

deserializer = TypeDeserializer()


def run():
    current_segment = int(datetime.utcnow().replace(second=0, microsecond=0).timestamp() + 10 * 60)  # scan the minute that is 10 minutes away, not the one that is already progressing

    count = 0

    for page in client.get_paginator('query').paginate(
            TableName=table_name,
            ProjectionExpression='pk,sk',
            KeyConditionExpression='pk = :s',
            ExpressionAttributeValues={
                ':s': {
                    'N': str(current_segment)
                }
            }):
        ids = []
        for item in page.get('Items', []):
            event = {k: deserializer.deserialize(v) for k, v in item.items()}
            ids.append({
                'pk': int(event['pk']),
                'sk': event['sk']
            })

        for chunk in make_chunks(ids, 200):
            invoke_lambda(os.environ.get('SCHEDULE_FUNCTION'), json.dumps(chunk).encode('utf-8'))

        count += page['Count']

    print('Batched %d entries' % count)

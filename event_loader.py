import json
import os
from datetime import timedelta, datetime

import boto3

lambda_client = boto3.client('lambda')
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aws-scheduler-events')


def run():
    now = datetime.utcnow()
    until = (now + timedelta(minutes=5)).isoformat()

    last_evaluated_key = None

    count = 0
    # emulated do while loop
    while True:

        response = load_data(until, last_evaluated_key)

        if response['Count'] == 0:
            break
        else:
            count += response['Count']

        ids = []
        for item in response['Items']:
            ids.append(item['id'])

        for chunk in make_chunks(ids, 200):
            payload = json.dumps(chunk).encode('ascii')
            lambda_client.invoke(
                FunctionName=os.environ.get('SCHEDULE_FUNCTION'),
                InvocationType='Event',
                Payload=payload
            )

        if 'LastEvaluatedKey' in response:
            print('Continuing at next page')
            last_evaluated_key = response['LastEvaluatedKey']
        else:
            print('Finished loading data')
            break

    print('Batched %d entries' % count)


# todo: move to util package
def make_chunks(l, chunk_length):
    # Yield successive n-sized chunks from l.
    for i in range(0, len(l), chunk_length):
        yield l[i:i + chunk_length]


def load_data(until, last_evaluated_key, limit=5000):
    if last_evaluated_key is None:
        response = table.query(
            IndexName=os.environ.get('INDEX_NAME'),
            KeyConditionExpression='#status = :st and #date < :until',
            ExpressionAttributeNames={"#status": "status", "#date": "date"},
            ExpressionAttributeValues={":until": until, ':st': 'NEW'},
            Limit=limit,
            ProjectionExpression='id'
        )
    else:
        response = table.query(
            IndexName=os.environ.get('INDEX_NAME'),
            KeyConditionExpression='#status = :st and #date < :until',
            ExpressionAttributeNames={"#status": "status", "#date": "date"},
            ExpressionAttributeValues={":until": until, ':st': 'NEW'},
            Limit=limit,
            ProjectionExpression='id',
            ExclusiveStartKey=last_evaluated_key
        )
    return response

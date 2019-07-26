import json
import math
import os
from datetime import datetime
from uuid import uuid4

import boto3

from db_helper import save_with_retry
from model import EventWrapper

lambda_client = boto3.client('lambda')


def handle(events):
    to_be_scheduled = []
    event_wrappers = []
    for event in events:
        event_wrapper = EventWrapper()
        event_wrapper.id = str(uuid4())
        event_wrapper.date = event['date']
        event_wrapper.event = json.dumps(event['event'])
        event_wrapper.arn = event['arn']

        # if the event has less than 10 minutes until execution, then fast track it
        if has_less_then_ten_minutes(event_wrapper.date):
            to_be_scheduled.append(event_wrapper.id)

        event_wrappers.append(event_wrapper)

    # we must save before delegating, because the downstream function will access the DB entity
    save_with_retry(event_wrappers)

    print('Fast track scheduling for %d entries' % len(to_be_scheduled))
    for chunk in make_chunks(to_be_scheduled, 200):
        payload = json.dumps(chunk).encode('ascii')
        lambda_client.invoke(
            FunctionName=os.environ.get('SCHEDULE_FUNCTION'),
            InvocationType='Event',
            Payload=payload
        )

    print('Processed %d entries' % len(events))


def has_less_then_ten_minutes(date):
    minutes = int(get_seconds_remaining(date) / 60)
    return minutes < 10


def get_seconds_remaining(date):
    now = datetime.utcnow()
    target = datetime.fromisoformat(date)
    delta = target - now
    return math.ceil(delta.total_seconds())


def make_chunks(l, chunk_length):
    # Yield successive n-sized chunks from l.
    for i in range(0, len(l), chunk_length):
        yield l[i:i + chunk_length]

import json
import math
import os
from datetime import datetime
from uuid import uuid4

import boto3

from db_helper import save_with_retry
from model import EventWrapper
from util import make_chunks

# todo: move into lambda client
lambda_client = boto3.client('lambda')


def publish_to_failure_topic(event):
    print('Event failed: %s' % event)


def handle(events):
    to_be_scheduled = []
    event_wrappers = []
    for event in events:
        print(event)
        if 'date' not in event or 'payload' not in event or 'target' not in event:
            publish_to_failure_topic(event)
            continue
        event_wrapper = EventWrapper()
        event_wrapper.id = str(uuid4())
        event_wrapper.date = event['date']
        if not isinstance(event['payload'], str):
            publish_to_failure_topic(event)
            continue
        event_wrapper.payload = event['payload']
        event_wrapper.target = event['target']
        if 'user' not in event:
            if 'true' == os.environ.get('ENFORCE_USER'):
                publish_to_failure_topic(event)
                continue
        else:
            event_wrapper.user = event['user']

        # if the event has less than 10 minutes until execution, then fast track it
        if has_less_then_ten_minutes(event_wrapper.date):
            to_be_scheduled.append(event_wrapper.id)

        event_wrappers.append(event_wrapper)

    # we must save before delegating, because the downstream function will access the DB entity
    save_with_retry(event_wrappers)

    print('Fast track scheduling for %d entries' % len(to_be_scheduled))
    for chunk in make_chunks(to_be_scheduled, 200):
        ids = json.dumps(chunk).encode('utf-8')
        lambda_client.invoke(
            FunctionName=os.environ.get('SCHEDULE_FUNCTION'),
            InvocationType='Event',
            Payload=ids
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

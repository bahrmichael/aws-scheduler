import json
import math
import os
from datetime import datetime

import boto3
from pynamodb.exceptions import DoesNotExist

from db_helper import save_with_retry
from model import EventWrapper
# todo: extract into queue client
sqs = boto3.client('sqs')


def handle(events):
    now = datetime.utcnow()
    successful_ids = []
    failed_ids = []

    to_be_scheduled = []

    events_by_id = {}

    for event_id in events:

        try:
            item = EventWrapper.get(event_id)
        except DoesNotExist:
            print('Event %s doesn\'t exist anymore' % event_id)
            continue

        events_by_id[event_id] = item

        delta = datetime.fromisoformat(item.date) - now
        delay = delta.total_seconds()
        rounded_delay = math.ceil(delay)
        if rounded_delay < 0:
            rounded_delay = 0

        to_be_scheduled.append({
            'Id': event_id,
            'MessageBody': json.dumps({
                'event': item.event,
                'arn': item.arn,
                'id': item.id
            }),
            'DelaySeconds': rounded_delay
        })

        # # DEV CODE REMOVE ME LATER
        # payload = json.loads(item.event)
        # if 'execution_time' in payload:
        #     execution_time = datetime.fromisoformat(payload['execution_time'])
        #     delta = int((datetime.utcnow() - execution_time).total_seconds() * 1000)
        #     if delta > 0:
        #         print(f'Delay: {delta}')

        if len(to_be_scheduled) == 10:
            successes, failures = send_to_sqs(to_be_scheduled)
            failed_ids.extend(failures)
            successful_ids.extend(successes)
            to_be_scheduled = []

    successes, failures = send_to_sqs(to_be_scheduled)
    failed_ids.extend(failures)
    successful_ids.extend(successes)

    print(f'Success: {len(successful_ids)}, Failed: {len(failed_ids)}')

    to_save = []
    for id in successful_ids:
        item = events_by_id[id]
        item.status = 'SCHEDULED'
        to_save.append(item)

    for id in failed_ids:
        item = events_by_id[id]
        item.status = 'FAILED'
        to_save.append(item)

    save_with_retry(to_save)


def send_to_sqs(to_be_scheduled):
    if len(to_be_scheduled) == 0:
        return [], []
    successful_ids = []
    failed_ids = []
    try:
        response = sqs.send_message_batch(
            QueueUrl=os.environ.get('QUEUE_URL'),
            Entries=to_be_scheduled
        )
        if 'Successful' in response:
            for element in response['Successful']:
                successful_ids.append(element['Id'])
        if 'Failed' in response:
            print(response['Failed'])
            for element in response['Failed']:
                failed_ids.append(element['Id'])

    except Exception as e:
        print(e)
        failed_ids = to_be_scheduled
    # todo: add logic to retry events that are in status FAILED, after x attempts put them into status ERROR
    return successful_ids, failed_ids

import json
import math
import os
from datetime import datetime

from pynamodb.exceptions import DoesNotExist

from db_helper import save_with_retry
from model import EventWrapper
from sns_client import publish_sns
from sqs_client import publish_sqs


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
                'payload': item.payload,
                'target': item.target,
                'id': item.id
            }),
            'DelaySeconds': rounded_delay
        })

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

        # todo: instead of publishing the error we should reschedule it automatically
        # can happen if sqs does not respond
        if item.failure_topic is not None:
            payload = {
                'error': 'ERROR',
                'event': item.payload
            }
            publish_sns(item.failure_topic, json.dumps(payload))

    save_with_retry(to_save)


def send_to_sqs(to_be_scheduled):
    if len(to_be_scheduled) == 0:
        return [], []
    successful_ids = []
    failed_ids = []
    try:
        response = publish_sqs(os.environ.get('QUEUE_URL'), to_be_scheduled)
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
    return successful_ids, failed_ids

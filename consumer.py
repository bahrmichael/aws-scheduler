import json
import math
import os
import time
from datetime import datetime
from uuid import uuid4

from model import table
from scheduler import schedule_events
from sns_client import publish_sns


def handle(events):
    received = datetime.utcnow()
    to_be_scheduled = []
    to_be_saved = []
    for event in events:
        if 'date' not in event:
            publish_to_failure_topic(event, 'date is required')
            print('error.date_required %s' % (json.dumps({'event': event})))
            continue
        if 'payload' not in event:
            publish_to_failure_topic(event, 'payload is required')
            print('error.payload_required %s' % (json.dumps({'event': event})))
            continue
        if 'target' not in event:
            publish_to_failure_topic(event, 'target is required')
            print('error.target_required %s' % (json.dumps({'event': event})))
            continue

        if not isinstance(event['payload'], str):
            publish_to_failure_topic(event, 'payload must be a string')
            print('error.payload_is_not_string %s' % (json.dumps({'event': event})))
            continue
        date = datetime.fromisoformat(event['date'])
        event_wrapper = {
            'pk': int(date.replace(second=0, microsecond=0).timestamp()),
            # the id separator has to be an underscore, because sqs IDs can only contain alphanumeric characters, hyphens and underscores
            'sk': f"{int(date.timestamp() * 1000)}_{str(uuid4())}",
            'time_to_live': int(date.timestamp() + 10 * 60),  # wait at least 10 minutes after the event should have gone out
            'date': event['date'],
            'payload': event['payload'],
            'target': event['target']
        }

        if 'failure_topic' in event:
            event_wrapper['failure_topic'] = event['failure_topic']

        if 'user' not in event:
            if os.environ.get('ENFORCE_USER'):
                publish_to_failure_topic(event, 'user is required')
                print('error.event_has_no_user %s' % (json.dumps({'event': event})))
                continue
        else:
            event_wrapper['user'] = event['user']

        # if the event has less than 10 minutes until execution, then fast track it
        if has_less_then_ten_minutes(event_wrapper['date']):
            to_be_scheduled.append(event_wrapper)
        else:
            to_be_saved.append(event_wrapper)
        print('event.consumed %s' % (json.dumps({'id': event_wrapper['sk'], 'timestamp': str(received)})))

    # we must save before delegating, because the downstream function will access the DB entity
    save_with_retry(to_be_saved)

    print('Fast track scheduling for %d entries' % len(to_be_scheduled))
    schedule_events(to_be_scheduled)

    print('Processed %d entries' % len(events))


def has_less_then_ten_minutes(date):
    minutes = int(get_seconds_remaining(date) / 60)
    return minutes < 10


def get_seconds_remaining(date):
    now = datetime.utcnow()
    target = datetime.fromisoformat(date)
    delta = target - now
    return math.ceil(delta.total_seconds())


def publish_to_failure_topic(event, reason):
    # todo: prepare against failure of publish sns
    print('Event failed: %s' % event)
    if 'failure_topic' in event:
        payload = {
            'error': reason,
            'event': event
        }
        publish_sns(event['failure_topic'], json.dumps(payload))


def save_with_retry(items):
    while True:
        if len(items) == 0:
            break
        item = items.pop(0)
        try:
            table.put_item(Item=item)
        except Exception as e:
            print(str(e))
            print('Delaying put of %s' % item.id)
            items.append(item)
            time.sleep(.200)

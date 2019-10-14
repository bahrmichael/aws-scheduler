import json
import time
from datetime import datetime

from db_helper import save_with_retry
from model import EventWrapper
from sns_client import publish_sns


def handle(items):
    failed_ids = []
    print(f'Processing {len(items)} records')

    # sort the items so that we process the earliest first
    items.sort(key=lambda x: x['date'])

    for item in items:
        event_id = item['id']

        # the event we received may have been scheduled early
        scheduled_execution = datetime.fromisoformat(item['date'])

        delay = (scheduled_execution - datetime.utcnow()).total_seconds()
        # remove another 10ms as there will be a short delay between the emitter, the target sns and its consumer
        delay -= 0.01
        # if there is a positive delay then wait until it's time
        if delay > 0:
            time.sleep(delay)

        try:
            publish_sns(item['target'], item['payload'])
            print('event.emitted %s' % (json.dumps({'id': event_id, 'timestamp': str(datetime.utcnow()), 'scheduled': str(scheduled_execution)})))
        except Exception as e:
            print(str(e))
            failed_ids.append(event_id)

    failed_items = []
    for event_id in failed_ids:
        try:
            event = EventWrapper.get(hash_key=event_id)
            event.status = 'FAILED'
            failed_items.append(event)

            # can happen if sqs does not respond
            if event.failure_topic is not None:
                payload = {
                    'error': 'ERROR',
                    'event': event.payload
                }
                publish_sns(event.failure_topic, json.dumps(payload))
        except Exception as e:
            print(f'Failure update: Skipped {event_id} because it doesn\'t exist anymore')
            print(str(e))

    save_with_retry(failed_items)

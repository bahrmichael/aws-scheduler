import json
import math
import os
from datetime import datetime

from boto3.dynamodb.conditions import Key

from db_helper import save_with_retry
from model import table
from sns_client import publish_sns
from sqs_client import publish_sqs


def handle(events):
    successful_ids = []
    failed_ids = []

    to_be_scheduled = []

    events_by_id = {}

    for event_id in events:

        event_response = table.query(
            KeyConditionExpression=Key('id').eq(event_id)
        )
        if event_response['Count'] == 0:
            print('Event %s doesn\'t exist anymore' % event_id)
            continue
        item = event_response['Items'][0]

        events_by_id[event_id] = item

        delta = datetime.fromisoformat(item['date']) - datetime.utcnow()
        delay = delta.total_seconds()
        rounded_delay = math.ceil(delay)
        if rounded_delay < 0:
            rounded_delay = 0

        # schedule the event a second earlier to help with delays in sqs/lambda cold start
        # the emitter will wait accordingly
        rounded_delay -= 1

        print(f'ID {event_id} is supposed to emit in {rounded_delay}s which is {delay - rounded_delay}s before target.')

        event = {
            'payload': item['payload'],
            'target': item['target'],
            'id': item['id'],
            'date': item['date']
        }
        if 'failure_topic' in item:
            event['failure_topic'] = item['failure_topic']
        sqs_message = {
            'Id': event_id,
            'MessageBody': json.dumps(event),
            'DelaySeconds': rounded_delay
        }
        to_be_scheduled.append(sqs_message)

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
        item['status'] = 'SCHEDULED'
        to_save.append(item)

    for id in failed_ids:
        item = events_by_id[id]
        item['status'] = 'FAILED'
        to_save.append(item)

        # todo: instead of publishing the error we should reschedule it automatically
        # can happen if sqs does not respond
        if 'failure_topic' in item:
            payload = {
                'error': 'ERROR',
                'event': item['payload']
            }
            publish_sns(item['failure_topic'], json.dumps(payload))

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
            print(f'ERROR: Failed to process entry: {response["Failed"]}')
            for element in response['Failed']:
                failed_ids.append(element['Id'])

    except Exception as e:
        print(str(e))
        failed_ids = to_be_scheduled
    return successful_ids, failed_ids

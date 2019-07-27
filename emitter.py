import json

from db_helper import delete_with_retry, save_with_retry
from model import EventWrapper

from sns_client import publish_sns


def handle(items):
    # todo: remove the message from the queue?
    processed_ids = []
    failed_ids = []
    print(f'Processing {len(items)} records')
    for item in items:
        event_id = item['id']
        try:
            if EventWrapper.count(hash_key=event_id) == 0:
                # if the event was already deleted from the database, then don't send it again
                continue
        except Exception as e:
            print(e)
            # if we can't determine if the event was already processed, then we'll send it
            # to make sure we have at least one delivery

        try:
            publish_sns(item['target'], item['payload'])
            processed_ids.append(event_id)
        except Exception as e:
            print(e)
            failed_ids.append(event_id)

    to_delete = []
    for event_id in processed_ids:
        try:
            to_delete.append(EventWrapper.get(hash_key=event_id))
        except Exception as e:
            print(f'Skipped {event_id} because it doesn\'t exist anymore')
            print(e)

    delete_with_retry(to_delete)

    failed_items = []
    for event_id in failed_ids:
        # todo: maybe also emit this to an error topic?
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
                # todo: let the publish_sns/sqs methods do the json dumping themselves if they encounter a non-string
                # i believe json.dumps("test") results in "test", if that's correct then we can always apply json.dumps()
                publish_sns(event.failure_topic, json.dumps(payload))
        except Exception as e:
            print(f'Skipped {event_id} because it doesn\'t exist anymore')
            print(e)

    save_with_retry(failed_items)


if __name__ == '__main__':
    print(json.dumps("123"))

import json

from consumer import handle as consumer_handle
from emitter import handle as emitter_handle
from event_loader import run
from scheduler import handle as schedule_batch_handle


def consumer(event, context):
    items = []
    for record in event['Records']:
        message = record['Sns']['Message']
        payload = json.loads(message)
        items.append(payload)
    consumer_handle(items)


def emitter(event, context):
    items = []
    for record in event['Records']:
        body = json.loads(record['body'])
        items.append(body)
    emitter_handle(items)


def scheduler(event, context):
    # the invocation of this lambda function passes the events array as a bytes
    # this lets us use the array directly
    schedule_batch_handle(event)


def event_loader(event, context):
    # this is triggered by a cronjob, no need to pass data
    run()

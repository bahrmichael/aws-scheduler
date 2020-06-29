import json
import time
from datetime import datetime

from sns_client import publish_sns

import boto3
cloudwatch = boto3.client('cloudwatch')


def put_metrics(metric, values, counts, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='serverless-scheduler',
        MetricData=[
            {
                'MetricName': metric,
                'Values': values,
                'Counts': counts,
                'Unit': unit
            },
        ]
    )


def put_metric(metric, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='serverless-scheduler',
        MetricData=[
            {
                'MetricName': metric,
                'Value': value,
                'Unit': unit
            },
        ]
    )


def handle(items):
    print(f'Processing {len(items)} records')

    # sort the items so that we process the earliest first
    items.sort(key=lambda x: x['date'])

    failed_events = []
    delays_ms = []
    for item in items:
        event_id = item['sk']

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
            now = datetime.utcnow()
            print('event.emitted %s' % (json.dumps({'sk': event_id, 'timestamp': str(now), 'scheduled': str(scheduled_execution)})))
            actual_delay = int((now - scheduled_execution).total_seconds() * 1000)
            print(f"{json.dumps({'event_id': event_id, 'timestamp': str(now), 'scheduled': str(scheduled_execution), 'delay': actual_delay, 'log_type': 'emit_delay'})}")
            delays_ms.append(actual_delay)
        except Exception as e:
            print(f"Failed to emit event {event_id}: {str(e)}")
            failed_events.append(item)

    delays_grouped = {}
    for delay in delays_ms:
        if delay not in delays_grouped:
            delays_grouped[delay] = 0
        delays_grouped[delay] += 1

    values = []
    counts = []
    for delay, count in delays_grouped.items():
        values.append(delay)
        counts.append(count)

    for event in failed_events:
        try:
            if event.failure_topic is not None:
                payload = {
                    'error': 'ERROR',
                    'event': event.payload
                }
                publish_sns(event.failure_topic, json.dumps(payload))
        except Exception as e:
            print(f"Failed to emit event {event['sk']} to failure topic: {str(e)}")

import sys
import time

import boto3

client = boto3.client('dynamodb')


def create_events_table():
    if len(sys.argv) < 2:
        print('Missing argument for stage.')
    stage = sys.argv[1]

    name = f'aws-scheduler-events-v2-{stage}'
    while True:
        response = client.list_tables()
        if name in response['TableNames']:
            print('Table %s already exists. Please delete it first. Waiting 5 seconds until trying again...' % name)
            time.sleep(5)
        else:
            break
    client.create_table(
        TableName=name,
        AttributeDefinitions=[
            {
                'AttributeName': 'pk',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'sk',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                'AttributeName': 'pk',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'sk',
                'KeyType': 'RANGE'
            }
        ],
        BillingMode='PAY_PER_REQUEST',
    )
    print(f'Creating table ...')
    client.get_waiter('table_exists').wait(TableName=name)
    client.update_time_to_live(
        TableName=name,
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'time_to_live'
        }
    )
    print('%s created' % name)


if __name__ == '__main__':
    create_events_table()

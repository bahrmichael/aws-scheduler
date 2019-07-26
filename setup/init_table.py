import boto3

client = boto3.client('dynamodb')


def events():
    name = 'aws-scheduler-events'
    response = client.list_tables()
    if name in response['TableNames']:
        print('Table %s already exists. Please delete it first.' % name)
        return
    client.create_table(
        TableName=name,
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'status',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'date',
                'AttributeType': 'S'
            },
        ],
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'status-date-index',
                'KeySchema': [
                    {
                        'AttributeName': 'status',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'date',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL',
                }
            }
        ],
        BillingMode='PAY_PER_REQUEST',
    )
    print('%s created' % name)


if __name__ == '__main__':
    events()

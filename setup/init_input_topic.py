import sys

import boto3

client = boto3.client('sns')


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Missing argument for stage.')
        exit()
    stage = sys.argv[1]

    name = f'scheduler-input-v2-{stage}'

    print(f'Creating topic {name}')
    create_response = client.create_topic(
        Name=name,
    )

    arn = create_response['TopicArn']
    print(f'Created topic {name} with arn {arn}')

    if len(sys.argv) == 3 and sys.argv[2] == 'public':
        print(f'Making {name} public')
        permission_response = client.add_permission(
            TopicArn=arn,
            Label=f'{name}-public-access',
            AWSAccountId=['*'],
            ActionName=['Publish']
        )

    print('Done')

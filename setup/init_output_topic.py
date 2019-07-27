import sys

import boto3

client = boto3.client('sns')


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Missing argument for stage.')
        exit()
    stage = sys.argv[1]

    name = f'scheduler-output-{stage}'

    print(f'Creating topic {name}')
    create_response = client.create_topic(
        Name=name,
    )

    arn = create_response['TopicArn']
    print(f'Created topic {name} with arn {arn}')

    if len(sys.argv) == 3:
        accountId = sys.argv[2]
    else:
        accountId = 256608350746
    print(f'Granting publish rights to {name} topic for accountId {accountId}')

    permission_response = client.add_permission(
        TopicArn=arn,
        Label=f'{name}-publish-access',
        AWSAccountId=[str(accountId)],
        ActionName=['Publish']
    )

    print('Done')

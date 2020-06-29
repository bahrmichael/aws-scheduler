import sys

import boto3

client = boto3.client('sns')


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('Missing argument for stage and role')
        exit()
    stage = sys.argv[1]

    name = f'scheduler-output-v2-{stage}'

    print(f'Creating topic {name}')
    create_response = client.create_topic(
        Name=name,
    )

    arn = create_response['TopicArn']
    print(f'Created topic {name} with arn {arn}')

    role = sys.argv[2]
    print(f'Granting publish rights to {name} topic for role {role}')

    permission_response = client.add_permission(
        TopicArn=arn,
        Label=f'{name}-publish-access',
        AWSAccountId=[str(role)],
        ActionName=['Publish']
    )

    print('Done')

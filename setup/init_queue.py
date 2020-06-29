import sys

import boto3

client = boto3.client('sqs')


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Missing argument for stage.')
        exit()
    stage = sys.argv[1]

    name = f'scheduler-queue-v2-{stage}'

    print(f'Creating queue {name}')
    create_response = client.create_queue(
        QueueName=name,
    )

    # todo: add redrive policy
    """
    RedrivePolicy - The string that includes the parameters for the dead-letter queue functionality of the source queue. For more information about the redrive policy and dead-letter queues, see Using Amazon SQS Dead-Letter Queues in the Amazon Simple Queue Service Developer Guide .
        deadLetterTargetArn - The Amazon Resource Name (ARN) of the dead-letter queue to which Amazon SQS moves messages after the value of maxReceiveCount is exceeded.
        maxReceiveCount - The number of times a message is delivered to the source queue before being moved to the dead-letter queue. When the ReceiveCount for a message exceeds the maxReceiveCount for a queue, Amazon SQS moves the message to the dead-letter-queue.
    """

    url = create_response['QueueUrl']
    print(f'Created topic {name} with arn {url}')

    print('Done')

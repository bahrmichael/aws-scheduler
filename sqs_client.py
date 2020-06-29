import boto3

client = boto3.client('sqs')


def publish_sqs(queue_url, to_be_scheduled):
    if len(to_be_scheduled) == 0:
        return [], []
    successful_ids = []
    failed_ids = []
    try:
        response = client.send_message_batch(
            QueueUrl=queue_url,
            Entries=to_be_scheduled
        )
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

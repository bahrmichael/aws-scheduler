import os

import boto3

table = boto3.resource('dynamodb').Table(f'aws-scheduler-events-{os.environ.get("STAGE")}')

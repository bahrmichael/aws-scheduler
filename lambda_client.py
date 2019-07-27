import boto3

client = boto3.client('lambda')


def invoke_lambda(function_name, payload):
    client.invoke(
        FunctionName=function_name,
        InvocationType='Event',
        Payload=payload
    )

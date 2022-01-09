# New Point In Time Scheduler

I've released a new scheduler service: [Check out the launch blog post](https://bahr.dev/2022/01/06/point-in-time-scheduler/).

# Old aws-scheduler

**!! This project is no longer actively maintained. !!**

**Warning**: I've rebuilt some parts of the system. If you followed the setup below before 01.06.20202, you have to recreate the database. For zero downtime I suggest you deploy the new version, switch over the input topic and then let the old version run dry before switching it off.

This project provides a solution to schedule large amounts of point in time events with a great time precision. See the Performance section for more details.

The two interfaces are two SNS topics. One for input and one for output. You send a scheduling payload to the input topic and at the specified datetime you will receive your data at the output topic. See the Usage section on how to attach your functions.

![Service Overview](https://github.com/bahrmichael/aws-scheduler/raw/master/pictures/overview.png)

## Usage

A quick start project is available at [aws-scheduler-testing](https://github.com/bahrmichael/aws-scheduler-testing).

### Setup
First of all you need an output topic that we can publish events to once the scheduled datetime arrives. To do this run `python setup/init_output_topic.py <stage>`. This will create a topic called `scheduler-output-<stage>` and grant our account the right to publish messages. You can see the added policy below.

```json
{
  "Sid": "scheduler-output-<stage>-publish-access",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:sts::256608350746:assumed-role/aws-scheduler-prod-us-east-1-lambdaRole/aws-scheduler-prod-emitter"
  },
  "Action": "SNS:Publish",
  "Resource": "arn:aws:sns:us-east-1:256608350746:scheduler-output-<stage>"
}
``` 

If you don't want to grant our emitter the right to publish, you can pass your own emitter role as a third argument.

```
Creating topic scheduler-output-<stage>
Created topic scheduler-output-<stage> with arn arn:aws:sns:us-east-1:<your-account-id>:scheduler-output-<stage>
Granting publish rights to scheduler-output-<stage> for role arn:aws:sts::256608350746:assumed-role/aws-scheduler-prod-us-east-1-lambdaRole/aws-scheduler-prod-emitter
Done
```

Write down the ARN of your output topic as you will need it for the input events.

Rerun this process with the command `python setup/init_failure_topic.py <stage>` to create a topic where the service can publish errors.

### Input
To schedule a trigger you have to publish an event which follows the structure below to the ARN of the input topic. You can find the ARN of our service in the SAAS Offer section.

```json
{
  "date": "utc timestamp following ISO 8601",
  "target": "arn of your sns output topic",
  "user": "some way we can get in touch with you",
  "payload": "any string payload",
  "failure_topic": "arn of an sns topic where the service can publish errors"
}
```

All fields except `failure_topic` are mandatory. Please make sure that the `payload` can be utf-8 encoded. If you submit an event that does not follow the spec, it will published to the `failure_topic`.

SNS messages must be strings. First string encode the json structure and then publish it to the input topic.

```python
# Python example
import json
import boto3

client = boto3.client('sns')

event = {
          "date": "2019-07-27T12:20:24.919071",
          "target": "arn:aws:sns:us-east-1:256608350746:scheduler-output-prod",
          "user": "Twitter @michabahr",
          "payload": "46607451-3e67-49bc-972b-425c150c5456"
        }

input_topic = 'arn:aws:sns:us-east-1:256608350746:scheduler-input-prod'
client.publish(TopicArn=input_topic, Message=json.dumps(event))
```

So far there is no batch publishing available for SNS. Make sure the event stays within the 256KB limit of SNS. We recommend that you only submit IDs and don't transfer any real data to the service.

### Output
Once the datetime specified in the payload is reached, the service will publish the content of the event field to your output topic. You can attach an AWS Lambda function to your topic to process the events. 

## Deploy it yourself
This section explains how you can deploy the service yourself. Once set up use it like shown above.

The following picture shows you the structure of the service.

![Detailed Overview](https://github.com/bahrmichael/aws-scheduler/raw/master/pictures/detailed.png)

### Prerequisites
You must have the following tools installed:
- serverless framework 1.48.3 or later
- node
- npm
- python3
- pip

Run `setup/init_table.py <stage>` to setup the database. Replace `<stage>` with the stage of your application.

Run `setup/init_input_topic.py <stage> [public]`. Replace `<stage>` with the stage of your application. You may append the parameter `public` to grant public publish rights.

Run `setup/init_queue.py <stage>`. Replace `<stage>` with the stage of your application.

### Deploy
1. Navigate into the project folder
2. With a tooling of your choice create and activate a venv
3. `pip install -r requirements.txt`
4. `npm i serverless-python-requirements`
5. `sls deploy`

Wait for the deployment to finish. Test the service by first attaching a function to the output topic and then send a few events to the input topic.

You can disable the `user` check on the input event for your own deployment with the `ENFORCE_USER` environment variable.
 
## Performance
We ran tests by sending events that included the scheduled timestamp in the payload. Once received we compared those timestamps with the current time.

In our results all events arrive within one second with a clear trend to stay well below 100ms.

![Distribution Over 5 Days](https://miro.medium.com/max/640/1*4LGtbE8CRYRwuqTNkjHiHQ.png)

The following chart show the amount of events received on the y axis and the distribution by delay on the x axis.

![Log Scaled Delay Times](https://miro.medium.com/max/640/1*LNkXRQ4Oaskb_DoDGpKJSg.png)

## Scalability

Based on our tests from the Performance section, we are confident that this stack can handle 100.000.000 events per month and might scale up to 500.000.000 events per month.

These numbers are not confirmed though, as that volume incurs significant AWS costs.

## Limitations
- Events may arrive more than once at the output topic.
- This approach costs more than using DynamoDB's TTL attribute. If delays of 30 minutes to 48 hours are acceptable for you, then check out [this article](https://medium.com/swlh/scheduling-irregular-aws-lambda-executions-through-dynamodb-ttl-attributes-acd397dfbad9). 

## Contributions
Contributions are welcome, both issues and code. Get in touch at twitter [@michabahr](https://twitter.com/michabahr) or create an issue.

## Example payloads

### Output topic
```json
{
  "EventSource": "aws:sns", 
  "EventVersion": "1.0", 
  "EventSubscriptionArn": "...", 
  "Sns": {
    "Type": "Notification", 
    "MessageId": "eccc1539-0867-5c6d-8b53-408f5b91b578", 
    "TopicArn": "arn:aws:sns:us-east-1:256608350746:scheduler-output-prod", 
    "Subject": null, 
    "Message": "my-message", 
    "Timestamp": "2019-07-27T13:29:26.405Z", 
    "SignatureVersion": "1", 
    "Signature": "...", 
    "SigningCertUrl": "...", 
    "UnsubscribeUrl": "...", 
    "MessageAttributes": {}
  }
}
```

## TODOs
- adjust pictures to show failure queue
- limitation of message size (10kb), also explain why
- secure the PoC with test
- add a safe guard that pulls messages from dead letter queues back into the circuit
- handling for messages that can't be utf-8 encoded

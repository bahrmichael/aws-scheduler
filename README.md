# aws-scheduler

This project provides a solution to schedule large amounts of point in time events with a great time precision. See the Performance section for more details.

The two interfaces are two SNS topics. One for input and one for output. You send a scheduling payload to the input topic and at the specified datetime you will receive your data at the output topic. See the Usage section on how to attach your functions.

![Service Overview](https://github.com/bahrmichael/aws-scheduler/raw/master/pictures/overview.png)

You can deploy this yourself or use our SAAS offer.

## SAAS Offer

While we're ironing things out you can use our service free of charge. Just publish an event to `arn:aws:sns:us-east-1:256608350746:scheduler-input-dev`.  This topic is public so anyone can publish to it. 

If you become a heavy user with more than 100.000 events per month we might want to get in touch with you, so make sure to fill out the `user` field with some way to contact you (email, twitter handle, ...).

## Usage

### Setup
First of all you need an output topic that we can publish events to once the scheduled datetime arrives. To do this go to the AWS Console, then open the service SNS and create a topic that includes the following access policy.

```json
    {
      "Sid": "HereComesYourSidName",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:sts::256608350746:assumed-role/aws-scheduler-dev-us-east-1-lambdaRole/aws-scheduler-dev-emitter"
      },
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:us-east-1:256608350746:scheduler-output-dev"
    }
``` 

This policy allows our emitter function to publish events to your topic which you can then process with e.g. AWS Lambda. 

Write down the ARN of your output topic as you will need it for the input events.

### Input
To schedule a trigger you have to publish an event which follows the structure below to the ARN of the input topic. You can find the ARN of our service in the SAAS Offer section.

```json
{
  "date": "utc timestamp following ISO 8601",
  "target": "arn of your output topic",
  "user": "some way we can get in touch with you",
  "payload": "any string payload"
}
```

All fields are mandatory. If you submit an event that does not follow the spec, it will be dropped. Future versions will improve on this.

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

Run `setup/init_table.py` to setup the database.

Create an SNS topic named `scheduler-input-{stage}` and a SQS queue named `scheduler-queue-{stage}`. Replace `{stage}` with the stage that you use for the serverless deployment, e.g. `dev`. Adjust the access policies as necessary.

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

Our results showed that most of the events arrive within one second of the specified datetime and the rest within the next few seconds.

The charts show the amount of events received on the y axis and the distribution by delay on the x axis.

![Regular Scaled 100000 events wihtin 10 minutes](https://github.com/bahrmichael/aws-scheduler/raw/master/pictures/regular-scaled-100k-10m.png)
![Log Scaled 100000 events wihtin 10 minutes](https://github.com/bahrmichael/aws-scheduler/raw/master/pictures/log-scaled-100k-10m.png)

## Limitations
Events may arrive more than once at the output topic.

## Contributions
Contributions are welcome, both issues and code. Get in touch at twitter [@michabahr](https://twitter.com/michabahr) or create an issue.

## TODOs
- test user check
- test with huge messages (first make as big as possible until fails, then execute them with more than 10 minutes target so they get bulked)
- prod deployment and update arns/policies
- use a proper logger
- secure the PoC with test
- include a failure queue and adjust the docs
- add a (video) guide on how to create a proper output queue
- add a safe guard that pulls messages from dead letter queues back into the circuit

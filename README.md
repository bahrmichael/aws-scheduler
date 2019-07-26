# aws-scheduler

## todos
- major duplication issues: i've scheduled 100k but received 240k measurements?


## howto to deploy
- create a virtual environment
- install serverless-requirements plugin
- pip install requirements.txt
- create topics
- sls deploy

note which version of sls you deployed this with (see https://github.com/serverless/serverless/issues/5345)

## delay infos
- show info on possible delays

## delivery guarantee infos
- show tests that prove that all messages are delivered

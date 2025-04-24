import json
import boto3
import os

sns = boto3.client('sns')
TOPIC_ARN = os.environ['SNS_TOPIC_ARN']  # Pass this as an environment variable

def lambda_handler(event, context):
    print("Received event:", event)
    body = json.loads(event['body'])
    email = body.get('email')

    if not email:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Email is required"})
        }

    response = sns.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol='email',
        Endpoint=email
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Subscription initiated. Check your email!"})
    }

#dsewc
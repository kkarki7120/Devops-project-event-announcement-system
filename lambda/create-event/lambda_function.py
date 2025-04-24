import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')

BUCKET = os.environ['S3_BUCKET_NAME']
FILE = 'events.json'
TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    print("Incoming event:", event)
    body = json.loads(event['body'])

    title = body.get('title')
    date = body.get('date')
    desc = body.get('description')

    if not title or not date or not desc:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing required fields"})
        }

    # Get current events
    try:
        response = s3.get_object(Bucket=BUCKET, Key=FILE)
        events = json.loads(response['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        events = []

    # Add new event
    new_event = {
        "title": title,
        "date": date,
        "description": desc
    }
    events.append(new_event)

    # Upload back to S3
    s3.put_object(
        Bucket=BUCKET,
        Key=FILE,
        Body=json.dumps(events),
        ContentType='application/json'
    )

    # Notify via SNS
    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject="New Event: " + title,
        Message=f"{title} on {date}\n{desc}"
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Event created and subscribers notified"})
    }

#wecwecwe
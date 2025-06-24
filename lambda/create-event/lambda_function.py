import json
import boto3
import os
from datetime import datetime
from urllib.parse import parse_qs
import base64

# Initialize AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Set environment variables
BUCKET = os.environ['S3_BUCKET_NAME']
FILE = 'events.json'
TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    print("Incoming event:", event)

    # Determine whether using Lambda Proxy Integration or not
    http_method = event.get('httpMethod') or event.get('routeKey', '').split(' ')[0]  # Fallback to routeKey

    # Handle GET request (Fetch events from S3)
    if http_method == 'GET':
        try:
            # Retrieve events from the S3 bucket
            response = s3.get_object(Bucket=BUCKET, Key=FILE)
            events = json.loads(response['Body'].read().decode('utf-8'))
            
            # Return events as a JSON response
            return {
                "statusCode": 200,
                "body": json.dumps(events)
            }
        except s3.exceptions.NoSuchKey:
            # If the events file doesn't exist, return an empty list
            return {
                "statusCode": 200,
                "body": json.dumps([])
            }
        except Exception as e:
            # If any error occurs, return an error response
            print(f"Error: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Error fetching events"})
            }

    # Handle POST request (Create a new event)
    elif http_method == 'POST':
        # Decode base64 body if necessary
        if event.get('isBase64Encoded'):
            decoded_body = base64.b64decode(event['body']).decode('utf-8')
        else:
            decoded_body = event['body']

        # Parse URL-encoded body
        parsed_body = parse_qs(decoded_body)

        # Get fields
        title = parsed_body.get('title', [None])[0]
        date = parsed_body.get('date', [None])[0]
        desc = parsed_body.get('description', [None])[0]

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

        # Upload updated events back to S3
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

    # Handle unsupported HTTP methods
    return {
        "statusCode": 405,
        "body": json.dumps({"message": "Method Not Allowed"})
    }

# lambda/handler.py
import json
import os
import requests
from datetime import datetime, timedelta
from mongoengine import connect, Document, StringField, FloatField, ListField, DateTimeField
import boto3

# MongoDB connection (assuming MongoDB URI provided via environment variables)
connect('item_locations', host=os.getenv('MONGO_URI', 'mongomock://localhost'))

# SNS and Kinesis clients
sns_client = boto3.client('sns')
kinesis_client = boto3.client('kinesis')

# MongoEngine Document with camelCase fields
class Item(Document):
    id = StringField(primary_key=True)
    name = StringField(required=True, max_length=50)
    postcode = StringField(required=True)
    latitude = FloatField(required=True)
    longitude = FloatField(required=True)
    directionFromNewYork = StringField(required=True, choices=["NE", "NW", "SE", "SW"])
    title = StringField(null=True)
    users = ListField(StringField(max_length=50))
    startDate = DateTimeField(required=True)

# Coordinates for New York (10001)
NY_COORDINATES = (40.7506, -73.9972)

def calculateDirection(lat, lon):
    lat_diff = lat - NY_COORDINATES[0]
    lon_diff = lon - NY_COORDINATES[1]
    if lat_diff > 0 and lon_diff > 0:
        return "NE"
    elif lat_diff > 0 and lon_diff < 0:
        return "NW"
    elif lat_diff < 0 and lon_diff > 0:
        return "SE"
    else:
        return "SW"

def main(event, context):
    # Validate Bearer token
    auth_header = event.get('headers', {}).get('Authorization', '')
    if not auth_header.startswith('Bearer ') or len(auth_header.split(' ')[1].strip()) == 0:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Unauthorized: Invalid Bearer token'})
        }

    body = json.loads(event.get('body', '{}'))
    name = body.get('name')
    title = body.get('title')
    users = body.get('users', [])
    start_date_str = body.get('startDate')

    if not name or len(name) >= 50:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Name is required and must be less than 50 characters'})
        }
    
    if not all(isinstance(user, str) and len(user) < 50 for user in users):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'All users must be strings and less than 50 characters'})
        }

    # Validate Start Date
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
            if start_date < datetime.now() + timedelta(weeks=1):
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'StartDate must be at least 1 week from today'})
                }
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid StartDate format. Use ISO format YYYY-MM-DDTHH:MM:SS'})
            }
    else:
        start_date = None

    postcode = event.get('queryStringParameters', {}).get('postcode')
    if not postcode:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Postcode is required'})
        }
    
    response = requests.get(f'https://api.zippopotam.us/us/{postcode}')
    if response.status_code != 200:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Postcode not found'})
        }
    data = response.json()
    lat = float(data['places'][0]['latitude'])
    lon = float(data['places'][0]['longitude'])
    direction = calculateDirection(lat, lon)
    
    # Save to MongoDB
    item = Item(
        name=name,
        postcode=postcode,
        latitude=lat,
        longitude=lon,
        directionFromNewYork=direction,
        title=title,
        users=users,
        startDate=start_date
    )
    item.save()
    
    log_message = {
        'postcode': postcode,
        'directionFromNewYork': direction
    }

    # Emit to SNS
    sns_client.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Message=json.dumps(log_message)
    )
    
    # Emit to Kinesis
    kinesis_client.put_record(
        StreamName=os.environ['KINESIS_STREAM_NAME'],
        Data=json.dumps(log_message),
        PartitionKey=postcode
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'postcode': postcode, 'directionFromNewYork': direction})
    }

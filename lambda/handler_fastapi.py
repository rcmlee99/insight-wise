# lambda/handler.py
import json
import os
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from mongoengine import connect, Document, StringField, FloatField, ListField, DateTimeField
from bson import ObjectId
import boto3

# MongoDB connection
connect('item_locations', host=os.getenv('MONGO_URI', 'mongomock://localhost'))

# AWS clients
sns_client = boto3.client('sns')
kinesis_client = boto3.client('kinesis')

app = FastAPI()

# Coordinates for New York (10001)
NY_COORDINATES = (40.7506, -73.9972)

class ItemModel(BaseModel):
    name: str = Field(..., max_length=50)
    title: Optional[str] = None
    users: List[str] = []
    startDate: Optional[datetime] = None
    postcode: str = Field(..., regex='^\d{5}$')

    @validator('users')
    def validate_users(cls, users):
        if not all(isinstance(user, str) and len(user) < 50 for user in users):
            raise ValueError('All users must be strings and less than 50 characters')
        return users

    @validator('startDate')
    def validate_start_date(cls, start_date):
        if start_date and start_date < datetime.now() + timedelta(weeks=1):
            raise ValueError('StartDate must be at least 1 week from today')
        return start_date


class Item(Document):
    name = StringField(required=True, max_length=50)
    title = StringField(null=True)
    users = ListField(StringField(max_length=50))
    startDate = DateTimeField(null=True)
    postcode = StringField(required=True)
    latitude = FloatField()
    longitude = FloatField()
    directionFromNewYork = StringField(choices=["NE", "NW", "SE", "SW"])


def calculate_direction(lat, lon):
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

async def validate_bearer_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Unauthorized: Invalid Bearer token')

@app.post('/items')
async def create_item(item: ItemModel, authorization: str = Depends(validate_bearer_token)):
    response = requests.get(f'https://api.zippopotam.us/us/{item.postcode}')
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail='Postcode not found')

    data = response.json()
    lat = float(data['places'][0]['latitude'])
    lon = float(data['places'][0]['longitude'])
    direction = calculate_direction(lat, lon)

    new_item = Item(
        name=item.name,
        title=item.title,
        users=item.users,
        startDate=item.startDate,
        postcode=item.postcode,
        latitude=lat,
        longitude=lon,
        directionFromNewYork=direction
    ).save()

    sns_client.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Message=json.dumps({'postcode': item.postcode, 'directionFromNewYork': direction})
    )

    kinesis_client.put_record(
        StreamName=os.environ['KINESIS_STREAM_NAME'],
        Data=json.dumps({'postcode': item.postcode, 'directionFromNewYork': direction}),
        PartitionKey=item.postcode
    )

    return JSONResponse(status_code=201, content={'id': str(new_item.id), 'message': 'Item created successfully.'})

# Other CRUD operations (GET, PATCH, DELETE) would follow similar FastAPI route definitions

# AWS Lambda handler
from mangum import Mangum
handler = Mangum(app)

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import json
from dateutil import parser
from decimal import Decimal
from bson import ObjectId
from .auth import verify_token

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, ObjectId):
            return str(o)
        return super(DecimalEncoder, self).default(o)

def validate_name_length(name: str) -> bool:
    return len(name) < 50

def validate_users(users: List[str]) -> tuple[bool, str]:
    if not isinstance(users, list):
        return False, "Users must be a list"
    if not users:
        return False, "Users list cannot be empty"

    for user in users:
        if not isinstance(user, str):
            return False, "Each user must be a string"
        if not validate_name_length(user):
            return False, f"User name '{user}' exceeds 50 characters"

    return True, ""

def validate_item(item: Dict[str, Any]) -> tuple[bool, str]:
    required_fields = ['name', 'postcode', 'startDate', 'users']

    # Check required fields
    for field in required_fields:
        if field not in item:
            return False, f"Missing required field: {field}"

    # Validate name length
    if not validate_name_length(item['name']):
        return False, "Name must be less than 50 characters"

    # Validate users list
    users_valid, users_error = validate_users(item['users'])
    if not users_valid:
        return False, users_error

    # Validate date
    try:
        start_date = parser.parse(item['startDate'])
        min_start_date = datetime.now(start_date.tzinfo) + timedelta(weeks=1)
        if start_date < min_start_date:
            return False, "Start date must be at least 1 week from now"
    except ValueError:
        return False, "Invalid date format"

    return True, ""

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def get_token_from_event(event: Dict[str, Any]) -> str:
    """Extract the JWT token from the API Gateway event"""
    if 'Authorization' not in event.get('headers', {}):
        raise ValueError("No Authorization header present")

    auth_header = event['headers']['Authorization']
    if not auth_header.startswith('Bearer '):
        raise ValueError("Invalid Authorization header format")

    return auth_header[7:]  # Remove 'Bearer ' prefix

def verify_auth(event: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify authentication token from the event"""
    try:
        token = get_token_from_event(event)
        verify_token(token)
        return True, ""
    except (ValueError, Exception) as e:
        return False, str(e)
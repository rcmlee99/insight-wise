import os
import pytest
from mongomock import MongoClient
from moto import mock_aws
import boto3
from shared.mongo_utils import set_mongo_collection

# Set AWS test credentials and region
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['MONGODB_URI'] = 'mongodb://localhost:27017'

# Set Cognito test environment variables
os.environ['USER_POOL_ID'] = 'test-pool'
os.environ['CLIENT_ID'] = 'test-client-id'
os.environ['TESTING'] = 'true'  # Enable test mode


@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture(scope='function')
def mongodb_client():
    """Create a mock MongoDB client for testing."""
    return MongoClient()


@pytest.fixture(scope='function')
def mongodb_collection(mongodb_client):
    """Create a mock MongoDB collection for testing."""
    db = mongodb_client.items_db
    collection = db.items
    # Inject the mock collection into mongo_utils
    set_mongo_collection(collection)
    yield collection
    collection.drop()  # Clean up after test
    set_mongo_collection(None)  # Reset the collection after test
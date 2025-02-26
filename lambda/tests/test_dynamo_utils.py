import os
import pytest
from unittest.mock import patch, MagicMock
from moto import mock_aws

# Set required environment variables for testing
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['ITEMS_TABLE'] = 'test-items-table'

from shared.dynamo_utils import (
    get_all_items,
    get_item,
    create_item,
    update_item,
    delete_item
)

@pytest.fixture
def mock_table():
    with patch('shared.dynamo_utils.get_table') as mock:
        yield mock

@pytest.fixture
def sample_item():
    return {
        'id': 'test-id',
        'name': 'Test Item',
        'description': 'Test Description'
    }

def test_get_all_items(mock_table):
    # Setup mock response
    mock_table.return_value.scan.return_value = {
        'Items': [
            {'id': '1', 'name': 'Item 1'},
            {'id': '2', 'name': 'Item 2'}
        ]
    }

    items = get_all_items()
    assert len(items) == 2
    mock_table.return_value.scan.assert_called_once()

    # Test empty response
    mock_table.return_value.scan.return_value = {}
    items = get_all_items()
    assert items == []

def test_get_item(mock_table, sample_item):
    # Test successful get
    mock_table.return_value.get_item.return_value = {'Item': sample_item}
    item = get_item('test-id')
    assert item == sample_item
    mock_table.return_value.get_item.assert_called_with(Key={'id': 'test-id'})

    # Test item not found
    mock_table.return_value.get_item.return_value = {}
    item = get_item('non-existent')
    assert item is None

def test_create_item(mock_table, sample_item):
    create_item(sample_item)
    mock_table.return_value.put_item.assert_called_with(Item=sample_item)

def test_update_item(mock_table):
    updates = {
        'name': 'Updated Name',
        'description': 'Updated Description'
    }

    update_item('test-id', updates)

    mock_table.return_value.update_item.assert_called_once()
    call_args = mock_table.return_value.update_item.call_args[1]

    assert call_args['Key'] == {'id': 'test-id'}
    assert '#name' in call_args['ExpressionAttributeNames']
    assert '#description' in call_args['ExpressionAttributeNames']
    assert ':name' in call_args['ExpressionAttributeValues']
    assert ':description' in call_args['ExpressionAttributeValues']

def test_delete_item(mock_table):
    delete_item('test-id')
    mock_table.return_value.delete_item.assert_called_with(Key={'id': 'test-id'})
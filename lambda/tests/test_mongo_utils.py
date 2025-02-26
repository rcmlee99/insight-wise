import os
import pytest
from mongomock import MongoClient
from pymongo.errors import PyMongoError, InvalidDocument
from shared.mongo_utils import (
    get_mongo_collection,
    get_all_items,
    get_item,
    create_item,
    update_item,
    delete_item,
    set_mongo_collection
)

# Test data
TEST_ITEM = {
    'id': 'test-id',
    'name': 'Test Item',
    'description': 'Test Description'
}

@pytest.fixture
def mock_mongo():
    """Create a mock MongoDB client and collection"""
    client = MongoClient()
    db = client.items_db
    collection = db.items

    # Create indexes
    collection.create_index([('id', 1)], unique=True)
    collection.create_index([('latitude', 1), ('longitude', 1)])

    # Set the mock collection
    set_mongo_collection(collection)

    yield collection

    # Cleanup
    collection.drop()
    set_mongo_collection(None)

def test_get_mongo_collection(mock_mongo):
    # Test successful collection initialization
    collection = get_mongo_collection()
    assert collection is not None
    assert collection == mock_mongo

def test_create_and_get_item(mock_mongo):
    # Test item creation
    create_item(TEST_ITEM)

    # Test get item
    item = get_item(TEST_ITEM['id'])
    assert item['id'] == TEST_ITEM['id']
    assert item['name'] == TEST_ITEM['name']

def test_get_all_items(mock_mongo):
    # Create multiple items
    items = [
        {'id': '1', 'name': 'Item 1'},
        {'id': '2', 'name': 'Item 2'},
        {'id': '3', 'name': 'Item 3'}
    ]
    for item in items:
        create_item(item)

    # Test get all items
    retrieved_items = get_all_items()
    assert len(retrieved_items) == 3
    assert all(item['id'] in ['1', '2', '3'] for item in retrieved_items)

def test_update_item(mock_mongo):
    # Create initial item
    create_item(TEST_ITEM)

    # Update item
    updates = {
        'name': 'Updated Name',
        'description': 'Updated Description'
    }

    update_item(TEST_ITEM['id'], updates)

    # Verify update
    updated_item = get_item(TEST_ITEM['id'])
    assert updated_item['name'] == updates['name']
    assert updated_item['description'] == updates['description']

def test_delete_item(mock_mongo):
    # Create item
    create_item(TEST_ITEM)

    # Delete item
    delete_item(TEST_ITEM['id'])

    # Verify deletion
    assert get_item(TEST_ITEM['id']) is None

def test_error_handling(mock_mongo):
    # Create test item
    create_item(TEST_ITEM)

    # Test duplicate key error
    with pytest.raises(Exception) as exc:
        create_item(TEST_ITEM)  # Duplicate ID
    assert "Duplicate Key Error" in str(exc.value)

    # Test invalid operations
    with pytest.raises(InvalidDocument) as exc:
        update_item(TEST_ITEM['id'], {'$invalid': 'update'})
    assert "$" in str(exc.value)

    # Test invalid ID format
    with pytest.raises(Exception) as exc:
        get_item(None)
    assert "Invalid ID" in str(exc.value)
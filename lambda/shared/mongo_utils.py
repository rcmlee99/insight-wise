import os
import logging
from typing import Dict, Any, List
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize MongoDB client
_client = None
_db = None
_items_collection = None

def get_mongo_collection():
    global _client, _db, _items_collection
    if _items_collection is None:
        _client = MongoClient(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017'))
        _db = _client.items_db
        _items_collection = _db.items

        # Ensure indexes
        try:
            _items_collection.create_index([('id', ASCENDING)], unique=True)
            logger.debug("Created unique index on 'id' field")

            # Optional: Add index for geospatial queries if needed
            _items_collection.create_index([('latitude', ASCENDING), ('longitude', ASCENDING)])
            logger.debug("Created index on latitude and longitude fields")
        except PyMongoError as e:
            logger.warning(f"Error creating indexes: {str(e)}")

    return _items_collection

def get_all_items() -> List[Dict[str, Any]]:
    try:
        return list(get_mongo_collection().find({}, {'_id': 0}))
    except PyMongoError as e:
        logger.error(f"Error getting all items: {str(e)}")
        raise

def get_item(item_id: str) -> Dict[str, Any]:
    try:
        if not item_id:
            raise Exception("Invalid ID: item_id cannot be None or empty")
        item = get_mongo_collection().find_one({'id': item_id}, {'_id': 0})
        return item if item else None
    except PyMongoError as e:
        logger.error(f"Error getting item {item_id}: {str(e)}")
        raise

def create_item(item: Dict[str, Any]) -> None:
    try:
        get_mongo_collection().insert_one(item)
    except PyMongoError as e:
        logger.error(f"Error creating item: {str(e)}")
        raise Exception("Duplicate Key Error" if "duplicate key error" in str(e).lower() else str(e))

def update_item(item_id: str, updates: Dict[str, Any]) -> None:
    try:
        if not item_id:
            raise Exception("Invalid ID: item_id cannot be None or empty")
        get_mongo_collection().update_one(
            {'id': item_id},
            {'$set': updates}
        )
    except PyMongoError as e:
        logger.error(f"Error updating item {item_id}: {str(e)}")
        raise

def delete_item(item_id: str) -> None:
    try:
        if not item_id:
            raise Exception("Invalid ID: item_id cannot be None or empty")
        get_mongo_collection().delete_one({'id': item_id})
    except PyMongoError as e:
        logger.error(f"Error deleting item {item_id}: {str(e)}")
        raise

# For testing purposes
def set_mongo_collection(collection):
    global _items_collection
    _items_collection = collection
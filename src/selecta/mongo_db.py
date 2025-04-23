import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Union, List, Optional, Dict, Any

async def connect_to_db(uri: str, db_name: str) -> Optional[AsyncIOMotorDatabase]:
    """Connect to MongoDB asynchronously and return the database object."""
    try:
        client = AsyncIOMotorClient(uri)
        db: AsyncIOMotorDatabase = client[db_name]
        logging.info(f"Connected to MongoDB!")
        return db
    except Exception as e:
        logging.error("Failed to connect to MongoDB:", exc_info=e)
        return None

async def query_collection(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    query: Dict[str, Any],
    projection: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """Query a collection with an optional filter and projection asynchronously."""
    collection: AsyncIOMotorCollection = db[collection_name]
    logging.info(f"Querying collection: {collection_name}...")
    cursor = collection.find(query, projection)
    results = await cursor.to_list(length=None)
    logging.info(f"Found {len(results)} results")
    return results

async def insert_documents(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    documents: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Union[Any, List[Any]]:
    """Insert one or many documents into a collection asynchronously."""
    collection: AsyncIOMotorCollection = db[collection_name]
    if isinstance(documents, dict):
        result = await collection.insert_one(documents)
        logging.info(f"Inserted 1 document into collection: {collection_name}")
        return result.inserted_id
    elif isinstance(documents, list):
        result = await collection.insert_many(documents)
        logging.info(f"Inserted {len(result.inserted_ids)} documents into collection: {collection_name}")
        return result.inserted_ids
    else:
        logging.error("Documents should be a dict or list of dicts")
        raise TypeError("Documents should be a dict or list of dicts")

async def update_documents(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    query: Dict[str, Any],
    update: Dict[str, Any],
    multiple: bool = False
) -> int:
    """Update one or many documents matching a query asynchronously."""
    collection: AsyncIOMotorCollection = db[collection_name]
    if multiple:
        result = await collection.update_many(query, update)
    else:
        result = await collection.update_one(query, update)
    logging.info(f"Updated {result.modified_count} document(s) in collection: {collection_name}")
    return result.modified_count

async def delete_documents(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    query: Dict[str, Any],
    multiple: bool = False
) -> int:
    """Delete one or many documents matching a query asynchronously."""
    collection: AsyncIOMotorCollection = db[collection_name]
    if multiple:
        result = await collection.delete_many(query)
    else:
        result = await collection.delete_one(query)
    logging.info(f"Deleted {result.deleted_count} document(s) in collection: {collection_name}")
    return result.deleted_count

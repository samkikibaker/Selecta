import logging

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult
from pymongo.errors import ConnectionFailure
from typing import Union, List, Optional, Dict, Any

def connect_to_db(uri: str, db_name: str) -> Optional[Database]:
    """Connect to MongoDB and return the database object."""
    try:
        client = MongoClient(uri)
        db: Database = client[db_name]
        logging.info(f"Connected to MongoDB!")
        return db
    except ConnectionFailure as e:
        logging.error("Failed to connect to MongoDB:", e)
        return None

def query_collection(
    db: Database,
    collection_name: str,
    query: Dict[str, Any],
    projection: Optional[Dict[str, int]]
) -> List[Dict[str, Any]]:
    """Query a collection with an optional filter and projection."""
    collection: Collection = db[collection_name]
    logging.info(f"Querying collection: {collection_name}...")
    results = collection.find(query, projection)
    logging.info(f"Found {len(list(results))} results")
    return list(results)

def insert_documents(
    db: Database,
    collection_name: str,
    documents: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Union[Any, List[Any]]:
    """Insert one or many documents into a collection."""
    collection: Collection = db[collection_name]
    if isinstance(documents, dict):
        result: InsertOneResult = collection.insert_one(documents)
        logging.info(f"Inserted 1 document into collection: {collection_name}")
        return result.inserted_id
    elif isinstance(documents, list):
        result: InsertManyResult = collection.insert_many(documents)
        logging.info(f"Inserted {len(result.inserted_ids)} documents into collection: {collection_name}")
        return result.inserted_ids
    else:
        logging.error("Documents should be a dict or list of dicts")
        raise TypeError("Documents should be a dict or list of dicts")

def update_documents(
    db: Database,
    collection_name: str,
    query: Dict[str, Any],
    update: Dict[str, Any],
    multiple: bool = False
) -> int:
    """Update one or many documents matching a query."""
    collection: Collection = db[collection_name]
    if multiple:
        result: UpdateResult = collection.update_many(query, update)
    else:
        result: UpdateResult = collection.update_one(query, update)
    logging.info(f"Updated {result.modified_count} document(s) in collection: {collection_name}")
    return result.modified_count

def delete_documents(
    db: Database,
    collection_name: str,
    query: Dict[str, Any],
    multiple: bool = False
) -> int:
    """Delete one or many documents matching a query."""
    collection: Collection = db[collection_name]
    if multiple:
        result: DeleteResult = collection.delete_many(query)
    else:
        result: DeleteResult = collection.delete_one(query)
    logging.info(f"Deleted {result.deleted_count} document(s) in collection: {collection_name}")
    return result.deleted_count

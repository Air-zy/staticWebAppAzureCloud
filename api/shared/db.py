import os
from azure.cosmos import CosmosClient, exceptions


def _get_container():
    client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
    db = client.get_database_client(os.environ["COSMOS_DATABASE"])
    return db.get_container_client(os.environ["COSMOS_CONTAINER"])


def get_user_by_email(email: str):
    container = _get_container()
    query = "SELECT * FROM c WHERE c.email = @email"
    params = [{"name": "@email", "value": email}]
    items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    return items[0] if items else None


def upsert_user(doc: dict):
    container = _get_container()
    container.upsert_item(doc)

import os
import json
import base64
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
table = dynamodb.Table(TABLE_NAME)


def _pk(user_id):
    return f"USER#{user_id}"


def _sk(upload_time, image_id):
    return f"IMAGE#{upload_time}#{image_id}"


def create_image_record(user_id, image_id, s3_key, upload_time, content_type, status, size=None):
    item = {
        "PK": _pk(user_id),
        "SK": _sk(upload_time, image_id),
        "image_id": image_id,
        "user_id": user_id,
        "s3_key": s3_key,
        "upload_time": upload_time,
        "content_type": content_type,
        "status": status,
        "is_deleted": False,
        "metadata_json": None,
    }
    if size:
        item["size"] = size

    table.put_item(Item=item)


def update_image_metadata(user_id, image_id, upload_time, size, content_type, metadata_json):
    table.update_item(
        Key={
            "PK": _pk(user_id),
            "SK": _sk(upload_time, image_id),
        },
        UpdateExpression="SET #st = :status, size = :size, content_type = :ct, metadata_json = :meta",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":status": "COMPLETED",
            ":size": size,
            ":ct": content_type,
            ":meta": metadata_json,
        },
    )


def get_image(user_id, image_id):
    # Query by PK and filter by image_id (since we don't have full SK without upload_time)
    response = table.query(
        KeyConditionExpression=Key("PK").eq(_pk(user_id)) & Key("SK").begins_with(f"IMAGE#"),
        FilterExpression=Attr("image_id").eq(image_id),
    )
    items = response.get("Items", [])
    return items[0] if items else None


def list_images(user_id, date_from=None, date_to=None, min_size=None, max_size=None, limit=20, cursor=None):
    key_condition = Key("PK").eq(_pk(user_id))

    # Date range via SK
    if date_from and date_to:
        key_condition = key_condition & Key("SK").between(
            f"IMAGE#{date_from}",
            f"IMAGE#{date_to}T23:59:59",
        )
    elif date_from:
        key_condition = key_condition & Key("SK").begins_with(f"IMAGE#{date_from}")

    # Build filter expression
    filter_expr = Attr("is_deleted").eq(False)

    if min_size is not None and max_size is not None:
        filter_expr = filter_expr & Attr("size").between(min_size, max_size)
    elif min_size is not None:
        filter_expr = filter_expr & Attr("size").gte(min_size)
    elif max_size is not None:
        filter_expr = filter_expr & Attr("size").lte(max_size)

    query_kwargs = {
        "KeyConditionExpression": key_condition,
        "FilterExpression": filter_expr,
        "Limit": limit,
        "ScanIndexForward": False,  # newest first
    }

    # Pagination cursor
    if cursor:
        last_key = json.loads(base64.b64decode(cursor).decode("utf-8"))
        query_kwargs["ExclusiveStartKey"] = last_key

    response = table.query(**query_kwargs)

    items = response.get("Items", [])
    last_evaluated = response.get("LastEvaluatedKey")

    next_cursor = None
    if last_evaluated:
        next_cursor = base64.b64encode(json.dumps(last_evaluated).encode()).decode()

    return {
        "items": [_format_item(i) for i in items],
        "next_cursor": next_cursor,
        "count": len(items),
    }


def soft_delete_image(user_id, image_id, upload_time):
    table.update_item(
        Key={
            "PK": _pk(user_id),
            "SK": _sk(upload_time, image_id),
        },
        UpdateExpression="SET is_deleted = :val",
        ExpressionAttributeValues={":val": True},
    )


def _decimal_to_native(obj):
    """Convert DynamoDB Decimal types to int or float."""
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def _format_item(item):
    return {
        "image_id": item.get("image_id"),
        "upload_time": item.get("upload_time"),
        "size": _decimal_to_native(item.get("size")),
        "content_type": item.get("content_type"),
        "status": item.get("status"),
        "s3_key": item.get("s3_key"),
    }

import os
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
table = dynamodb.Table(TABLE_NAME)


def update_image_metadata(user_id, image_id, upload_time, size, content_type, metadata_json):
    """
    Updates the image record to COMPLETED with extracted metadata.
    Looks up the record by user_id + image_id since we need the full SK.
    """
    # First find the record to get the exact SK (upload_time may differ slightly)
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("IMAGE#"),
        FilterExpression=Attr("image_id").eq(image_id),
    )

    items = response.get("Items", [])
    if not items:
        raise ValueError(f"No DynamoDB record found for image_id={image_id}")

    record = items[0]

    table.update_item(
        Key={
            "PK": record["PK"],
            "SK": record["SK"],
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

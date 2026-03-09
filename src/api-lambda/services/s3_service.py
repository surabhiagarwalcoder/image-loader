import os
import boto3

s3_client = boto3.client("s3")
BUCKET_NAME = os.environ["S3_BUCKET"]
PRESIGNED_URL_EXPIRY = 900  # 15 minutes


def generate_presigned_upload_url(s3_key, content_type):
    url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )
    return url


def generate_presigned_download_url(s3_key):
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )
    return url


def delete_s3_object(s3_key):
    s3_client.delete_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
    )


def get_object_metadata(s3_key):
    response = s3_client.head_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
    )
    return {
        "size": response["ContentLength"],
        "content_type": response["ContentType"],
        "last_modified": response["LastModified"].isoformat(),
    }

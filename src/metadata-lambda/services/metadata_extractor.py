import boto3
from datetime import datetime, timezone

s3_client = boto3.client("s3")


def extract_metadata(bucket, s3_key, file_size):
    """
    Extracts metadata from the S3 object.
    Extends easily for EXIF, ML tagging etc.
    """
    # Fetch S3 object head for content type and other attributes
    head = s3_client.head_object(Bucket=bucket, Key=s3_key)

    content_type = head.get("ContentType", "application/octet-stream")
    last_modified = head.get("LastModified", datetime.now(timezone.utc))

    metadata = {
        "content_type": content_type,
        "size": file_size,
        "upload_time": last_modified.isoformat(),
        "s3_key": s3_key,
        "exif": extract_exif(bucket, s3_key, content_type),
    }

    return metadata


def extract_exif(bucket, s3_key, content_type):
    """
    Placeholder for EXIF extraction.
    Can be extended with Pillow or Rekognition.
    """
    if content_type not in ("image/jpeg", "image/jpg"):
        return {}

    # Example: use Pillow for EXIF
    # response = s3_client.get_object(Bucket=bucket, Key=s3_key)
    # image_data = response["Body"].read()
    # image = Image.open(BytesIO(image_data))
    # exif_data = image._getexif() or {}
    # return {ExifTags.TAGS.get(k, k): str(v) for k, v in exif_data.items()}

    return {}

import json
import sys
import os

# Add modules/ folder to path so pip-installed dependencies are found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))

from services.metadata_extractor import extract_metadata
from services.dynamo_service import update_image_metadata
from utils.logger import get_logger

logger = get_logger()


def lambda_handler(event, context):
    """
    Triggered by S3 event when image is uploaded.
    Extracts metadata and updates DynamoDB record.
    """
    for record in event.get("Records", []):
        s3_info = record.get("s3", {})
        bucket = s3_info["bucket"]["name"]
        s3_key = s3_info["object"]["key"]
        file_size = s3_info["object"].get("size", 0)

        logger.info(f"Processing: bucket={bucket} key={s3_key}")

        try:
            # Parse user_id and image_id from s3_key
            # s3_key format: user_id/YYYY-MM/image_id
            parts = s3_key.split("/")
            user_id = parts[0]
            image_id = parts[-1]

            # Extract metadata from the image
            metadata = extract_metadata(bucket, s3_key, file_size)

            # Update DynamoDB record to COMPLETED
            update_image_metadata(
                user_id=user_id,
                image_id=image_id,
                upload_time=metadata["upload_time"],
                size=file_size,
                content_type=metadata["content_type"],
                metadata_json=metadata,
            )

            logger.info(f"Successfully processed image: {image_id}")

        except Exception as e:
            logger.error(f"Failed to process {s3_key}: {e}")
            raise  # Re-raise so SQS/DLQ can handle retry

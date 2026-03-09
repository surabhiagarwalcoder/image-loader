import uuid
from datetime import datetime, timezone
from services.s3_service import generate_presigned_upload_url
from services.dynamo_service import create_image_record
from utils.response import success_response, error_response


def handle_upload_url(event, user_id):
    try:
        body = event.get("body") or "{}"
        import json
        body = json.loads(body)

        content_type = body.get("content_type", "image/jpeg")
        file_size = body.get("size")  # optional, client can send expected size

        image_id = str(uuid.uuid4())
        upload_time = datetime.now(timezone.utc).isoformat()
        s3_key = f"{user_id}/{upload_time[:7]}/{image_id}"  # user/YYYY-MM/uuid

        # Create DynamoDB record with UPLOADING status
        create_image_record(
            user_id=user_id,
            image_id=image_id,
            s3_key=s3_key,
            upload_time=upload_time,
            content_type=content_type,
            size=file_size,
        )

        # Generate pre-signed S3 PUT URL
        upload_url = generate_presigned_upload_url(s3_key, content_type)

        return success_response(200, {
            "image_id": image_id,
            "upload_url": upload_url,
            "s3_key": s3_key,
        })

    except Exception as e:
        print(f"Upload URL error: {e}")
        return error_response(500, "Failed to generate upload URL")

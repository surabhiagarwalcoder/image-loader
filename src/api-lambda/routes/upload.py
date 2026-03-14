import json
import uuid
import base64
import requests
from datetime import datetime
from services.s3_service import generate_presigned_upload_url
from services.dynamo_service import create_image_record
from utils.response import success_response, error_response


def handle_upload_image(event, user_id):
    """
    Client sends image binary + user_id.
    Internally: generates presigned URL, uses it to upload to S3.
    Client never sees the presigned URL.
    """
    try:
        # ── Parse content type from headers ───────────────────────────────
        headers = event.get("headers") or {}
        content_type = headers.get("content-type") or headers.get("Content-Type") or "image/jpeg"

        # ── Decode image body ──────────────────────────────────────────────
        body = event.get("body")
        is_base64 = event.get("isBase64Encoded", False)

        if not body:
            return error_response(400, "Image body is required")

        # API Gateway ALWAYS sends binary as base64
        # even if isBase64Encoded flag is missing
        try:
            image_data = base64.b64decode(body)
        except Exception:
            # fallback if body is already raw bytes
            image_data = body if isinstance(body, bytes) else body.encode("utf-8")

        # ── Build S3 key ───────────────────────────────────────────────────
        image_id = str(uuid.uuid4())
        month_prefix = datetime.utcnow().strftime("%Y-%m")
        s3_key = f"{user_id}/{month_prefix}/{image_id}"

        # ── Step 1: Generate presigned URL internally ──────────────────────
        presigned_url = generate_presigned_upload_url(
            s3_key=s3_key,
            content_type=content_type
        )

        # ── Step 2: Use presigned URL to upload to S3 ──────────────────────
        upload_response = requests.put(
            presigned_url,
            data=image_data,
            headers={"Content-Type": content_type}
        )

        if upload_response.status_code != 200:
            return error_response(500, f"S3 upload failed: {upload_response.status_code}")

        # ── Step 3: Save metadata to DynamoDB ─────────────────────────────
        upload_time = datetime.utcnow().isoformat()
        create_image_record(
            user_id=user_id,
            image_id=image_id,
            s3_key=s3_key,
            upload_time=upload_time,
            content_type=content_type,
            status="COMPLETED",
            size=len(image_data)
        )

        # ── Return success — client never sees presigned URL ───────────────
        return success_response(200, {
            "image_id": image_id,
            "size": len(image_data),
            "upload_time": upload_time,
            "status": "COMPLETED"
        })

    except Exception as e:
        print(f"Upload error: {e}")
        return error_response(500, f"Upload failed: {str(e)}")
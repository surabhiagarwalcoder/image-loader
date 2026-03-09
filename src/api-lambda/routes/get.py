from services.dynamo_service import get_image, _decimal_to_native
from services.s3_service import generate_presigned_download_url
from utils.response import success_response, error_response


def handle_get_image(event, user_id):
    try:
        image_id = event["pathParameters"]["image_id"]

        record = get_image(user_id=user_id, image_id=image_id)

        if not record:
            return error_response(404, "Image not found")

        if record.get("is_deleted"):
            return error_response(404, "Image not found")

        # Generate pre-signed GET URL — client downloads directly from S3
        download_url = generate_presigned_download_url(record["s3_key"])

        return success_response(200, {
            "image_id": record["image_id"],
            "upload_time": record["upload_time"],
            "size": _decimal_to_native(record.get("size")),
            "content_type": record.get("content_type"),
            "status": record.get("status"),
            "metadata": record.get("metadata_json"),
            "download_url": download_url,
        })

    except Exception as e:
        print(f"Get image error: {e}")
        return error_response(500, "Failed to get image")

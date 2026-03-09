from services.dynamo_service import get_image, soft_delete_image
from services.s3_service import delete_s3_object
from utils.response import success_response, error_response


def handle_delete_image(event, user_id):
    try:
        image_id = event["pathParameters"]["image_id"]

        record = get_image(user_id=user_id, image_id=image_id)

        if not record:
            return error_response(404, "Image not found")

        if record.get("is_deleted"):
            return error_response(404, "Image not found")

        # Delete from S3 first, then mark deleted in DynamoDB
        delete_s3_object(record["s3_key"])
        soft_delete_image(user_id=user_id, image_id=image_id, upload_time=record["upload_time"])

        return success_response(200, {"message": "Image deleted successfully"})

    except Exception as e:
        print(f"Delete image error: {e}")
        return error_response(500, "Failed to delete image")

import json
import sys
import os

# Add modules/ folder to path so pip-installed dependencies are found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))

from routes.upload import handle_upload_url
from routes.list import handle_list_images
from routes.get import handle_get_image
from routes.delete import handle_delete_image
from utils.auth import extract_user_id
from utils.response import error_response

ROUTES = {
    ("POST", "/images/upload-url"): handle_upload_url,
    ("GET", "/images"):             handle_list_images,
    ("GET", "/images/{image_id}"):  handle_get_image,
    ("DELETE", "/images/{image_id}"): handle_delete_image,
}


def lambda_handler(event, context):
    try:
        method = event["httpMethod"]
        path = event["resource"]  # API Gateway resource path e.g. /images/{image_id}

        user_id = extract_user_id(event)
        if not user_id:
            return error_response(401, "Unauthorized")

        handler_fn = ROUTES.get((method, path))
        if not handler_fn:
            return error_response(404, "Route not found")

        return handler_fn(event, user_id)

    except Exception as e:
        print(f"Unhandled error: {e}")
        return error_response(500, "Internal server error")

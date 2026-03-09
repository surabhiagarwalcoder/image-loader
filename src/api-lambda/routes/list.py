from services.dynamo_service import list_images
from utils.response import success_response, error_response


def handle_list_images(event, user_id):
    try:
        params = event.get("queryStringParameters") or {}

        # Date range filter (via SK)
        date_from = params.get("from")  
        date_to = params.get("to")    

        # Size range filter (via FilterExpression)
        min_size = int(params["min_size"]) if params.get("min_size") else None
        max_size = int(params["max_size"]) if params.get("max_size") else None

        # Pagination
        limit = int(params.get("limit", 20))
        cursor = params.get("cursor")        # base64 encoded LastEvaluatedKey

        result = list_images(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            min_size=min_size,
            max_size=max_size,
            limit=limit,
            cursor=cursor,
        )

        return success_response(200, result)

    except Exception as e:
        print(f"List images error: {e}")
        return error_response(500, "Failed to list images")

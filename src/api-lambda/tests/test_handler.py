import json
import pytest
from unittest.mock import patch, MagicMock
import handler  # import once at module level

# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_event(method, resource, path_params=None, body=None, headers=None):
    return {
        "httpMethod": method,
        "resource": resource,
        "pathParameters": path_params or {},
        "body": json.dumps(body) if body else None,
        "headers": headers or {"x-user-id": "test-user-123"},
        "queryStringParameters": None,
        "requestContext": {},
    }

MOCK_CONTEXT = MagicMock()

# ─── Test: Routing ─────────────────────────────────────────────────────────────

class TestRouting:

    def test_post_upload_url_routes_correctly(self):
        mock_fn = MagicMock(return_value={"statusCode": 200, "body": "{}"})
        handler.ROUTES[("POST", "/images/upload-url")] = mock_fn
        event = make_event("POST", "/images/upload-url")
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        mock_fn.assert_called_once()
        assert response["statusCode"] == 200

    def test_get_images_routes_correctly(self):
        mock_fn = MagicMock(return_value={"statusCode": 200, "body": "{}"})
        handler.ROUTES[("GET", "/images")] = mock_fn
        event = make_event("GET", "/images")
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        mock_fn.assert_called_once()
        assert response["statusCode"] == 200

    def test_get_image_by_id_routes_correctly(self):
        mock_fn = MagicMock(return_value={"statusCode": 200, "body": "{}"})
        handler.ROUTES[("GET", "/images/{image_id}")] = mock_fn
        event = make_event("GET", "/images/{image_id}", path_params={"image_id": "abc-123"})
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        mock_fn.assert_called_once()
        assert response["statusCode"] == 200

    def test_delete_image_routes_correctly(self):
        mock_fn = MagicMock(return_value={"statusCode": 200, "body": "{}"})
        handler.ROUTES[("DELETE", "/images/{image_id}")] = mock_fn
        event = make_event("DELETE", "/images/{image_id}", path_params={"image_id": "abc-123"})
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        mock_fn.assert_called_once()
        assert response["statusCode"] == 200

# ─── Test: Auth ────────────────────────────────────────────────────────────────

class TestAuth:

    def test_returns_401_when_no_user_id(self):
        event = make_event("GET", "/images", headers={})
        # patch extract_user_id at the handler module level (where it's used)
        with patch("handler.extract_user_id", return_value=None):
            response = handler.lambda_handler(event, MOCK_CONTEXT)
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["error"] == "Unauthorized"

    def test_passes_user_id_from_header(self):
        mock_fn = MagicMock(return_value={"statusCode": 200, "body": "{}"})
        handler.ROUTES[("GET", "/images")] = mock_fn
        event = make_event("GET", "/images", headers={"x-user-id": "user-abc"})
        with patch("handler.extract_user_id", return_value="user-abc"):
            handler.lambda_handler(event, MOCK_CONTEXT)
        args = mock_fn.call_args[0]
        assert args[1] == "user-abc"

    def test_passes_user_id_from_cognito_claims(self):
        mock_fn = MagicMock(return_value={"statusCode": 200, "body": "{}"})
        handler.ROUTES[("GET", "/images")] = mock_fn
        event = make_event("GET", "/images", headers={})
        event["requestContext"] = {
            "authorizer": {"claims": {"sub": "cognito-user-999"}}
        }
        with patch("handler.extract_user_id", return_value="cognito-user-999"):
            handler.lambda_handler(event, MOCK_CONTEXT)
        args = mock_fn.call_args[0]
        assert args[1] == "cognito-user-999"

# ─── Test: Unknown Routes ──────────────────────────────────────────────────────

class TestUnknownRoutes:

    def test_returns_404_for_unknown_route(self):
        event = make_event("GET", "/unknown-path")
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "Route not found"

    def test_returns_404_for_wrong_method(self):
        event = make_event("PUT", "/images")
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        assert response["statusCode"] == 404

    def test_returns_404_for_patch_method(self):
        event = make_event("PATCH", "/images/{image_id}")
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        assert response["statusCode"] == 404

# ─── Test: Error Handling ──────────────────────────────────────────────────────

class TestErrorHandling:

    def test_returns_500_when_handler_raises_exception(self):
        mock_fn = MagicMock(side_effect=Exception("Something went wrong"))
        handler.ROUTES[("GET", "/images")] = mock_fn
        event = make_event("GET", "/images")
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"] == "Internal server error"

    def test_returns_500_when_event_missing_http_method(self):
        event = {"resource": "/images", "headers": {"x-user-id": "test-user-123"}}
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        assert response["statusCode"] == 500

    def test_returns_500_when_event_missing_resource(self):
        event = {"httpMethod": "GET", "headers": {"x-user-id": "test-user-123"}}
        response = handler.lambda_handler(event, MOCK_CONTEXT)
        assert response["statusCode"] == 500
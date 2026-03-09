import os

def extract_user_id(event):
    """
    Extracts user_id from API Gateway request context.
    In production with Cognito, user identity is injected automatically.
    For testing without Cognito, falls back to a header or default test user.
    """
    try:
        # Production: Cognito JWT authorizer injects claims
        claims = (
            event.get("requestContext", {})
                 .get("authorizer", {})
                 .get("claims", {})
        )
        user_id = claims.get("sub")
        if user_id:
            return user_id

        # Testing: allow passing user_id via header
        headers = event.get("headers") or {}
        user_id = headers.get("x-user-id") or headers.get("X-User-Id")
        if user_id:
            return user_id

        # Fallback for local/dev testing
        if os.environ.get("ENVIRONMENT") == "dev":
            return "test-user-123"

        return None

    except Exception as e:
        print(f"Auth extraction error: {e}")
        return None

import sys
import os

# Add src/api-lambda to path so pytest can find handler, routes, services etc.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set required environment variables before any module is imported
os.environ.setdefault("S3_BUCKET", "test-bucket")
os.environ.setdefault("DYNAMODB_TABLE", "test-table")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
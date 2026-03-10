import json
import pytest
from unittest.mock import patch, MagicMock
import handler

# ─── Helpers ──────────────────────────────────────────────────────────────────

MOCK_CONTEXT = MagicMock()

def make_s3_event(bucket, s3_key, size=1024):
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": s3_key, "size": size},
                }
            }
        ]
    }

MOCK_METADATA = {
    "upload_time": "2024-01-15T10:30:00Z",
    "content_type": "image/jpeg",
    "width": 1920,
    "height": 1080,
}

# ─── Test: Happy Path ──────────────────────────────────────────────────────────

class TestHappyPath:

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_processes_single_record_successfully(self, mock_extract, mock_update):
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg", size=2048)
        handler.lambda_handler(event, MOCK_CONTEXT)
        mock_extract.assert_called_once_with("my-bucket", "user-123/2024-01/img-abc.jpg", 2048)
        mock_update.assert_called_once()

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_parses_user_id_from_s3_key(self, mock_extract, mock_update):
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg")
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["user_id"] == "user-123"

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_parses_image_id_from_s3_key(self, mock_extract, mock_update):
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg")
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["image_id"] == "img-abc.jpg"

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_passes_correct_metadata_to_dynamo(self, mock_extract, mock_update):
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg", size=5000)
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["upload_time"] == MOCK_METADATA["upload_time"]
        assert kw["content_type"] == MOCK_METADATA["content_type"]
        assert kw["size"] == 5000
        assert kw["metadata_json"] == MOCK_METADATA

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_processes_multiple_records(self, mock_extract, mock_update):
        event = {
            "Records": [
                {"s3": {"bucket": {"name": "bucket"}, "object": {"key": "u1/2024-01/img1.jpg", "size": 100}}},
                {"s3": {"bucket": {"name": "bucket"}, "object": {"key": "u2/2024-01/img2.jpg", "size": 200}}},
                {"s3": {"bucket": {"name": "bucket"}, "object": {"key": "u3/2024-01/img3.jpg", "size": 300}}},
            ]
        }
        handler.lambda_handler(event, MOCK_CONTEXT)
        assert mock_extract.call_count == 3
        assert mock_update.call_count == 3

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_handles_zero_size_file(self, mock_extract, mock_update):
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg", size=0)
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["size"] == 0

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_handles_missing_size_defaults_to_zero(self, mock_extract, mock_update):
        event = {
            "Records": [
                {"s3": {"bucket": {"name": "bucket"}, "object": {"key": "u1/2024-01/img1.jpg"}}}
            ]
        }
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["size"] == 0


# ─── Test: Empty / No Records ─────────────────────────────────────────────────

class TestEmptyEvents:

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata")
    def test_handles_empty_records_list(self, mock_extract, mock_update):
        event = {"Records": []}
        handler.lambda_handler(event, MOCK_CONTEXT)
        mock_extract.assert_not_called()
        mock_update.assert_not_called()

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata")
    def test_handles_missing_records_key(self, mock_extract, mock_update):
        event = {}
        handler.lambda_handler(event, MOCK_CONTEXT)
        mock_extract.assert_not_called()
        mock_update.assert_not_called()


# ─── Test: Error Handling ──────────────────────────────────────────────────────

class TestErrorHandling:

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", side_effect=Exception("S3 read failed"))
    def test_raises_exception_when_extract_metadata_fails(self, mock_extract, mock_update):
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg")
        with pytest.raises(Exception, match="S3 read failed"):
            handler.lambda_handler(event, MOCK_CONTEXT)

    @patch("handler.update_image_metadata", side_effect=Exception("DynamoDB write failed"))
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_raises_exception_when_dynamo_update_fails(self, mock_extract, mock_update):
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg")
        with pytest.raises(Exception, match="DynamoDB write failed"):
            handler.lambda_handler(event, MOCK_CONTEXT)

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", side_effect=Exception("fail"))
    def test_does_not_swallow_exception(self, mock_extract, mock_update):
        """Exceptions must propagate so SQS/DLQ can handle retries."""
        event = make_s3_event("my-bucket", "user-123/2024-01/img-abc.jpg")
        with pytest.raises(Exception):
            handler.lambda_handler(event, MOCK_CONTEXT)
        mock_update.assert_not_called()


# ─── Test: S3 Key Parsing ──────────────────────────────────────────────────────

class TestS3KeyParsing:

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_parses_standard_key_format(self, mock_extract, mock_update):
        event = make_s3_event("bucket", "user-999/2024-06/photo.png")
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["user_id"] == "user-999"
        assert kw["image_id"] == "photo.png"

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_image_id_is_last_part_of_key(self, mock_extract, mock_update):
        event = make_s3_event("bucket", "user-abc/2024-01/subdir/my-image.jpg")
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["image_id"] == "my-image.jpg"

    @patch("handler.update_image_metadata")
    @patch("handler.extract_metadata", return_value=MOCK_METADATA)
    def test_user_id_is_first_part_of_key(self, mock_extract, mock_update):
        event = make_s3_event("bucket", "u-xyz/2024-12/img.webp")
        handler.lambda_handler(event, MOCK_CONTEXT)
        kw = mock_update.call_args[1]
        assert kw["user_id"] == "u-xyz"
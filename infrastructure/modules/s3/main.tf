resource "aws_s3_bucket" "images" {
  bucket = "${var.project}-${var.environment}-images-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket                  = aws_s3_bucket.images.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "GET"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Fix: filter {} is required in AWS provider v5+
resource "aws_s3_bucket_lifecycle_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

# Only wire S3 → Lambda notification when Lambda ARN is provided
resource "aws_s3_bucket_notification" "images" {
  count  = var.metadata_lambda_arn != "" ? 1 : 0
  bucket = aws_s3_bucket.images.id

  lambda_function {
    lambda_function_arn = var.metadata_lambda_arn
    events              = ["s3:ObjectCreated:*"]
  }
}

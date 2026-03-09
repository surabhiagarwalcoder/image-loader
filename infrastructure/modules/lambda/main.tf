locals {
  api_lambda_name      = "${var.project}-${var.environment}-api"
  metadata_lambda_name = "${var.project}-${var.environment}-metadata"

  # Zips are built by CI/CD pipeline before terraform runs
  api_lambda_zip      = "${path.root}/../../api-lambda.zip"
  metadata_lambda_zip = "${path.root}/../../metadata-lambda.zip"
}

# ─── API Lambda ───────────────────────────────────────────────────────────────

resource "aws_lambda_function" "api" {
  function_name    = local.api_lambda_name
  role             = var.api_lambda_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = local.api_lambda_zip
  source_code_hash = filebase64sha256(local.api_lambda_zip)
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
      S3_BUCKET      = var.s3_bucket_name
      ENVIRONMENT    = var.environment
    }
  }
}

resource "aws_cloudwatch_log_group" "api_lambda" {
  name              = "/aws/lambda/${local.api_lambda_name}"
  retention_in_days = 14
}

# ─── Metadata Lambda ──────────────────────────────────────────────────────────

resource "aws_lambda_function" "metadata" {
  function_name    = local.metadata_lambda_name
  role             = var.metadata_lambda_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = local.metadata_lambda_zip
  source_code_hash = filebase64sha256(local.metadata_lambda_zip)
  timeout          = 60
  memory_size      = 512

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
      S3_BUCKET      = var.s3_bucket_name
      ENVIRONMENT    = var.environment
    }
  }
}

resource "aws_cloudwatch_log_group" "metadata_lambda" {
  name              = "/aws/lambda/${local.metadata_lambda_name}"
  retention_in_days = 14
}

# Allow S3 to invoke the metadata Lambda
resource "aws_lambda_permission" "s3_invoke_metadata" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.metadata.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.images_bucket_arn
}

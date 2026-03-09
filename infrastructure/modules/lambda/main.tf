locals {
  api_lambda_name      = "${var.project}-${var.environment}-api"
  metadata_lambda_name = "${var.project}-${var.environment}-metadata"
}

# ─── Package Lambda source code ───────────────────────────────────────────────

data "archive_file" "api_lambda" {
  type        = "zip"
  source_dir  = "${path.root}/../src/api-lambda"
  output_path = "${path.module}/builds/api-lambda.zip"
  excludes    = []
}

data "archive_file" "metadata_lambda" {
  type        = "zip"
  source_dir  = "${path.root}/../src/metadata-lambda"
  output_path = "${path.module}/builds/metadata-lambda.zip"
  excludes    = []
}

# ─── API Lambda ───────────────────────────────────────────────────────────────

resource "aws_lambda_function" "api" {
  function_name    = local.api_lambda_name
  role             = var.api_lambda_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.api_lambda.output_path
  source_code_hash = data.archive_file.api_lambda.output_base64sha256
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
  filename         = data.archive_file.metadata_lambda.output_path
  source_code_hash = data.archive_file.metadata_lambda.output_base64sha256
  timeout          = 60
  memory_size      = 512  # Higher for image processing

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

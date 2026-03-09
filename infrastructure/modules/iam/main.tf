data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ─── API Lambda Role ───────────────────────────────────────────────────────────

resource "aws_iam_role" "api_lambda" {
  name               = "${var.project}-${var.environment}-api-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "api_lambda" {
  name   = "api-lambda-policy"
  role   = aws_iam_role.api_lambda.id
  policy = data.aws_iam_policy_document.api_lambda_policy.json
}

data "aws_iam_policy_document" "api_lambda_policy" {
  # CloudWatch Logs
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # S3 — pre-signed URL generation, delete
  statement {
    actions   = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
    resources = ["${var.s3_bucket_arn}/*"]
  }

  # DynamoDB — read + write
  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
    ]
    resources = [var.dynamodb_table_arn]
  }
}

resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  role       = aws_iam_role.api_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ─── Metadata Lambda Role ──────────────────────────────────────────────────────

resource "aws_iam_role" "metadata_lambda" {
  name               = "${var.project}-${var.environment}-metadata-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "metadata_lambda" {
  name   = "metadata-lambda-policy"
  role   = aws_iam_role.metadata_lambda.id
  policy = data.aws_iam_policy_document.metadata_lambda_policy.json
}

data "aws_iam_policy_document" "metadata_lambda_policy" {
  # CloudWatch Logs
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # S3 — read only (head + get for metadata extraction)
  statement {
    actions   = ["s3:GetObject", "s3:HeadObject"]
    resources = ["${var.s3_bucket_arn}/*"]
  }

  # DynamoDB — update only
  statement {
    actions   = ["dynamodb:UpdateItem", "dynamodb:Query"]
    resources = [var.dynamodb_table_arn]
  }
}

resource "aws_iam_role_policy_attachment" "metadata_lambda_basic" {
  role       = aws_iam_role.metadata_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

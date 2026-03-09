resource "aws_dynamodb_table" "images" {
  name         = "${var.project}-${var.environment}-images"
  billing_mode = "PAY_PER_REQUEST"  # On-demand, auto scales
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # Enable point-in-time recovery for production safety
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project}-${var.environment}-images"
  }
}

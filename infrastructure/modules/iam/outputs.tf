output "api_lambda_role_arn" {
  value = aws_iam_role.api_lambda.arn
}

output "metadata_lambda_role_arn" {
  value = aws_iam_role.metadata_lambda.arn
}

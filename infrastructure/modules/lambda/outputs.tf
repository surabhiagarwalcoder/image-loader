output "api_lambda_arn" {
  value = aws_lambda_function.api.arn
}

output "api_lambda_name" {
  value = aws_lambda_function.api.function_name
}

output "metadata_lambda_arn" {
  value = aws_lambda_function.metadata.arn
}

output "metadata_lambda_permission_id" {
  value = aws_lambda_permission.s3_invoke_metadata.id
}

output "api_lambda_invoke_arn" {
  value = aws_lambda_function.api.invoke_arn
}
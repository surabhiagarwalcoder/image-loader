output "table_name" {
  value = aws_dynamodb_table.images.name
}

output "table_arn" {
  value = aws_dynamodb_table.images.arn
}

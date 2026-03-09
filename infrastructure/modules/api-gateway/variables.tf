variable "environment" {}
variable "project" {}
variable "api_lambda_arn" {}
variable "api_lambda_name" {}

variable "api_lambda_invoke_arn" {
  default = ""
}

variable "cognito_user_pool_arn" {
  default = ""
}

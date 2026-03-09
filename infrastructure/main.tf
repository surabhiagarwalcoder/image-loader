module "s3" {
  source      = "./modules/s3"
  environment = var.environment
  project     = var.project
}

module "dynamodb" {
  source      = "./modules/dynamodb"
  environment = var.environment
  project     = var.project
}

module "iam" {
  source             = "./modules/iam"
  environment        = var.environment
  project            = var.project
  s3_bucket_arn      = module.s3.bucket_arn
  dynamodb_table_arn = module.dynamodb.table_arn
}

module "lambda" {
  source                   = "./modules/lambda"
  environment              = var.environment
  project                  = var.project
  s3_bucket_name           = module.s3.bucket_name
  dynamodb_table_name      = module.dynamodb.table_name
  api_lambda_role_arn      = module.iam.api_lambda_role_arn
  metadata_lambda_role_arn = module.iam.metadata_lambda_role_arn
  images_bucket_arn        = module.s3.bucket_arn
}

module "api_gateway" {
  source                = "./modules/api-gateway"
  environment           = var.environment
  project               = var.project
  api_lambda_arn        = module.lambda.api_lambda_arn
  api_lambda_name       = module.lambda.api_lambda_name
  api_lambda_invoke_arn = module.lambda.api_lambda_invoke_arn
}

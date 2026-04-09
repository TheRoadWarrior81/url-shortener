output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.urls.name
}

output "lambda_shorten_arn" {
  description = "Shorten Lambda function ARN"
  value       = aws_lambda_function.shorten.arn
}

output "lambda_redirect_arn" {
  description = "Redirect Lambda function ARN"
  value       = aws_lambda_function.redirect.arn
}
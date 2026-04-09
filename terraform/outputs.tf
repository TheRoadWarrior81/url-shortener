output "api_endpoint" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "cloudfront_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "frontend_url" {
  value = "https://${var.subdomain}.${var.domain_name}"
}
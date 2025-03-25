# API Gateway
resource "aws_apigatewayv2_api" "s3_photos_viewer" {
  name          = "s3-photos-viewer"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "s3_photos_viewer" {
  api_id      = aws_apigatewayv2_api.s3_photos_viewer.id
  name        = "$default" 
  auto_deploy = true

  #access_log_setting {
  #  destination_arn = aws_cloudwatch_log_group.s3_photos_viewer.arn
  #  format          = jsonencode({ "requestId" : "$context.requestId", "ip" : "$context.identity.sourceIp", "requestTime" : "$context.requestTime", "httpMethod" : "$context.httpMethod", "routeKey" : "$context.routeKey", "status" : "$context.status", "protocol" : "$context.protocol", "responseLength" : "$context.responseLength" })
  #}
}

resource "aws_apigatewayv2_integration" "lambda" {
  depends_on = [
     aws_lambda_function.s3_photos_viewer
  ]

  api_id             = aws_apigatewayv2_api.s3_photos_viewer.id
  integration_uri    = aws_lambda_function.s3_photos_viewer.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}


resource "aws_apigatewayv2_route" "proxy" {
  depends_on = [
     aws_apigatewayv2_integration.lambda
  ]
  api_id      = aws_apigatewayv2_api.s3_photos_viewer.id
  route_key   = "$default"
  target      = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}



# Custom Domain

# Custom Domain
resource "aws_apigatewayv2_domain_name" "photos" {
  domain_name = var.domain_name  

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.photos.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}



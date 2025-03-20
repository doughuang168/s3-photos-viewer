# API Gateway
resource "aws_api_gateway_rest_api" "s3_photos_viewer" {
  name = "s3-photos-viewer"
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.s3_photos_viewer.id
  parent_id   = aws_api_gateway_rest_api.s3_photos_viewer.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.s3_photos_viewer.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.s3_photos_viewer.id
  resource_id = aws_api_gateway_method.proxy.resource_id
  http_method = aws_api_gateway_method.proxy.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.s3_photos_viewer.invoke_arn
}

resource "aws_api_gateway_deployment" "s3_photos_viewer" {
   depends_on = [
     aws_api_gateway_integration.lambda,
   ]

   rest_api_id = aws_api_gateway_rest_api.s3_photos_viewer.id
   #stage_name  = "prod" #var.stage #Warning: Argument is deprecated
}

resource "aws_api_gateway_stage" "s3_photos_viewer" {
  deployment_id = aws_api_gateway_deployment.s3_photos_viewer.id
  rest_api_id   = aws_api_gateway_rest_api.s3_photos_viewer.id
  stage_name    = "prod"  ##var.stage
}

###
#resource "aws_api_gateway_deployment" "s3_photos_viewer" {
#  rest_api_id = aws_api_gateway_rest_api.s3_photos_viewer.id
#  stage_name  = "prod"
#}
#╷
#│ Warning: Argument is deprecated
#│
#│   with aws_api_gateway_deployment.s3_photos_viewer,
#│   on api-gateway.tf line 31, in resource "aws_api_gateway_deployment" "s3_photos_viewer":
#│   31:   stage_name  = "prod"
#│
#│ stage_name is deprecated. Use the aws_api_gateway_stage resource instead.
#│
#│ (and one more similar warning elsewhere)
#╵


/***
# Custom Domain
resource "aws_api_gateway_domain_name" "photos" {
  domain_name              = "photos.mydomain.com"
  regional_certificate_arn = aws_acm_certificate_validation.photos.certificate_arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_base_path_mapping" "photos" {
  api_id      = aws_api_gateway_rest_api.s3_photos_viewer.id
  stage_name  = aws_api_gateway_deployment.s3_photos_viewer.stage_name
  domain_name = aws_api_gateway_domain_name.photos.domain_name
}
***/

output "base_url" {
  value = "${aws_api_gateway_deployment.s3_photos_viewer.invoke_url}"
  ##value = "${aws_api_gateway_deployment.s3_photo_viewer.invoke_url}/${var.resource_name}"
}


terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }

  backend "http" {}

  required_version = ">= 1.3.0"

}

provider "aws" {
  region = var.region
}

data aws_caller_identity current {}
 
locals {
  account_id          = data.aws_caller_identity.current.account_id
  ecr_repository_name = var.ecr_repository_name
  ecr_image_tag       = var.ecr_image_tag
}


# Lambda Function
resource "aws_lambda_function" "s3_photos_viewer" {
  function_name = local.ecr_repository_name 
  role          = aws_iam_role.lambda_exec.arn
  image_uri     ="${local.account_id}.dkr.ecr.us-east-1.amazonaws.com/${local.ecr_repository_name}:${local.ecr_image_tag}"
  package_type  = "Image"
  timeout       = 30

  environment {
    variables = {
      BUCKET_NAME = "your-s3-bucket-name" # Replace with your S3 bucket name
    }
  }
}


resource "aws_lambda_permission" "apigw" {
   depends_on = [
     aws_apigatewayv2_route.proxy
   ]

   statement_id  = "AllowAPIGatewayInvoke"
   action        = "lambda:InvokeFunction"
   function_name = aws_lambda_function.s3_photos_viewer.function_name
   principal     = "apigateway.amazonaws.com"

   # The "/*/*" portion grants access from any method on any resource
   # within the API Gateway REST API.
   source_arn = "${aws_apigatewayv2_api.s3_photos_viewer.execution_arn}/*/*"
}


# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role-${local.ecr_repository_name}" 

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}


resource "aws_cloudwatch_log_group" "lambda_log_group" {
  # Creates a CloudWatch Log Group for CloudTrail logs
  name = "/aws/lambda/${local.ecr_repository_name}" 
}

# Attach the required policy to the IAM Role
resource "aws_iam_role_policy_attachment" "lambda_role_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_exec.name
}


# Custom Domain
resource "aws_apigatewayv2_domain_name" "photos" {
  domain_name = var.domain_name

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.photos.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

# ACM Certificate
resource "aws_acm_certificate" "photos" {
  domain_name       = var.domain_name  
  validation_method = "DNS"
}

resource "aws_route53_record" "photos_validation" {
  for_each = {
    for dvo in aws_acm_certificate.photos.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  name    = each.value.name
  records = [each.value.record]
  type    = each.value.type
  zone_id = data.aws_route53_zone.mydomain.zone_id
  ttl     = 60
}

resource "aws_acm_certificate_validation" "photos" {
  certificate_arn         = aws_acm_certificate.photos.arn
  validation_record_fqdns = [for record in aws_route53_record.photos_validation : record.fqdn]
}


data "aws_route53_zone" "mydomain" {
  name         = var.mydomain  
  private_zone = false
}


resource "aws_route53_record" "photos" {
  name    = aws_apigatewayv2_domain_name.photos.domain_name
  type    = "A"
  zone_id = data.aws_route53_zone.mydomain.zone_id

  alias {
    name                   = aws_apigatewayv2_domain_name.photos.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.photos.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}


terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.10.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-2"
}

resource "aws_iam_role" "lambda_role" {
  name = "tixel_scraper_lambda_role"

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

resource "aws_iam_role_policy" "lambda_policy" {
  name = "tixel_scraper_lambda_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::tixel-data",
          "arn:aws:s3:::tixel-data/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Create a timestamp for 3 months from now
resource "time_rotating" "function_expiry" {
  rotation_days = 90 # 3 months
}

# Create a null resource that will trigger the destroy when the timestamp expires
resource "time_static" "expiry_check" {
  triggers = {
    # This will update when the rotation timestamp changes
    expiry = time_rotating.function_expiry.rotation_rfc3339
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lambda_function" "tixel_scraper" {
  filename         = "dist/lambda.zip"
  function_name    = "tixel-scraper"
  role            = aws_iam_role.lambda_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.12"
  timeout         = 300  # 5 minutes
  memory_size     = 256

  environment {
    variables = {
      PYTHONPATH = "/var/task"
      EXPIRY_DATE = time_rotating.function_expiry.rotation_rfc3339
    }
  }

  # This will force the function to be destroyed when the timestamp expires
  depends_on = [time_static.expiry_check]
}

# Optional: Add CloudWatch Event Rule to trigger the Lambda on a schedule
resource "aws_cloudwatch_event_rule" "scheduled_trigger" {
  name                = "trigger-tixel-scraper-6hours"
  description         = "Trigger Tixel scraper Lambda function every 6 hours"
  schedule_expression = "rate(6 hours)"  # Run every 6 hours
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.scheduled_trigger.name
  target_id = "TixelScraperLambda"
  arn       = aws_lambda_function.tixel_scraper.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowCloudWatchTrigger"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tixel_scraper.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_trigger.arn
}

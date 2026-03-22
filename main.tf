terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1"
}

# S3 Bucket
resource "aws_s3_bucket" "data_platform" {
  bucket = "nicol-data-trust-project"
}

# DynamoDB Table
resource "aws_dynamodb_table" "validation_logs" {
  name         = "data-validation-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_name"
  range_key    = "timestamp"

  attribute {
    name = "file_name"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }
}

# SNS Topic
resource "aws_sns_topic" "alerts" {
  name = "data-validation-alerts"
}
resource "aws_s3_bucket" "irb_documents" {
  bucket = "hipaa-irb-documents-${var.environment}"
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.data_encryption.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }

  logging {
    target_bucket = aws_s3_bucket.access_logs.id
    target_prefix = "logs/"
  }
}

resource "aws_s3_bucket_policy" "irb_documents" {
  bucket = aws_s3_bucket.irb_documents.id
  policy = data.aws_iam_policy_document.irb_documents.json
}

resource "aws_s3_bucket" "access_logs" {
  bucket = "hipaa-access-logs-${var.environment}"
  acl    = "log-delivery-write"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.data_encryption.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
} 
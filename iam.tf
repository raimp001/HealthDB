data "aws_iam_policy_document" "irb_documents" {
  statement {
    actions   = ["s3:*"]
    effect    = "Deny"
    resources = ["${aws_s3_bucket.irb_documents.arn}/*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    effect    = "Allow"
    resources = ["${aws_s3_bucket.irb_documents.arn}/*"]
    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.ec2_instance_role.arn]
    }
  }
} 
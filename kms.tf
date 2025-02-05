data "aws_iam_policy_document" "kms_policy" {
  statement {
    sid    = "EnableIAMPermissions"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowServiceAccess"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = [
        "rds.amazonaws.com",
        "s3.amazonaws.com",
        "ec2.amazonaws.com"
      ]
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = ["*"]
  }
}

data "aws_caller_identity" "current" {} 
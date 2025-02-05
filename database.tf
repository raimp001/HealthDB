module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "5.1.0"

  identifier = "hipaa-db"

  engine               = "postgres"
  engine_version       = "13.7"
  family               = "postgres13"
  major_engine_version = "13"
  instance_class       = "db.m5.large"

  allocated_storage     = 100
  max_allocated_storage = 500

  storage_encrypted = true
  kms_key_id        = aws_kms_key.data_encryption.arn

  db_name  = "researchplatform"
  username = var.db_username
  password = var.db_password
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.app.id]

  backup_retention_period = 35
  maintenance_window      = "Mon:00:00-Mon:03:00"
  backup_window           = "03:00-06:00"

  parameters = [
    {
      name  = "rds.force_ssl"
      value = "1"
    }
  ]
} 
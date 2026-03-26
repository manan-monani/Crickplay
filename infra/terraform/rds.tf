# ============================================
# RDS PostgreSQL (Managed)
# Replaces local Docker Postgres
# ============================================

resource "aws_db_subnet_group" "postgres" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-postgres"
  engine         = "postgres"
  engine_version = "14.15"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Free tier / dev settings
  multi_az            = false
  publicly_accessible = false
  skip_final_snapshot = true

  # Performance insights (disabled for free tier)
  performance_insights_enabled = false

  # Backups (1 day for free tier)
  backup_retention_period = 1
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Parameter group for RLS support
  parameter_group_name = aws_db_parameter_group.postgres.name

  tags = {
    Name = "${var.project_name}-postgres"
  }
}

# Custom parameter group
resource "aws_db_parameter_group" "postgres" {
  name   = "${var.project_name}-pg14-params"
  family = "postgres14"

  # Enable shared_preload_libraries for pg_stat_statements
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  # Log slow queries (> 1 second)
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Name = "${var.project_name}-pg-params"
  }
}

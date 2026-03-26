# ============================================
# Outputs
# ============================================

output "ec2_public_ip" {
  description = "Public IP of the app server"
  value       = aws_eip.app_server.public_ip
}

output "ec2_ssh_command" {
  description = "SSH command to connect to the app server"
  value       = "ssh -i crickplay-key.pem ubuntu@${aws_eip.app_server.public_ip}"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_connection_string" {
  description = "PostgreSQL connection string (without password)"
  value       = "postgresql+asyncpg://${var.db_username}:****@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
}

output "s3_bucket" {
  description = "S3 data bucket name"
  value       = aws_s3_bucket.data.bucket
}

output "kafka_ui_url" {
  description = "Kafka UI URL"
  value       = "http://${aws_eip.app_server.public_ip}:8081"
}

output "mlflow_url" {
  description = "MLflow tracking server URL"
  value       = "http://${aws_eip.app_server.public_ip}:5001"
}

output "fastapi_url" {
  description = "FastAPI docs URL (after deploying app)"
  value       = "http://${aws_eip.app_server.public_ip}:8000/docs"
}

output "private_key_path" {
  description = "Path to the generated SSH private key"
  value       = local_file.private_key.filename
}

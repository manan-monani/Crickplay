# ============================================
# EC2 App Server
# Runs Docker Compose (Kafka, Zookeeper, Kafka-UI, MLflow, FastAPI)
# ============================================

# Generate SSH key pair
resource "tls_private_key" "app_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "app_key" {
  key_name   = var.ec2_key_name
  public_key = tls_private_key.app_key.public_key_openssh

  tags = {
    Name = "${var.project_name}-keypair"
  }
}

# Save private key locally
resource "local_file" "private_key" {
  content         = tls_private_key.app_key.private_key_pem
  filename        = "${path.module}/crickplay-key.pem"
  file_permission = "0400"
}

# Get latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instance
resource "aws_instance" "app_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  key_name               = aws_key_pair.app_key.key_name
  subnet_id              = aws_subnet.public_a.id
  vpc_security_group_ids = [aws_security_group.app_server.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  # 30GB root volume
  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name = "${var.project_name}-root-volume"
    }
  }

  # User data script — installs Docker, Docker Compose, Python, Git, and clones project
  user_data = base64encode(templatefile("${path.module}/userdata.sh", {
    db_host     = aws_db_instance.postgres.address
    db_port     = aws_db_instance.postgres.port
    db_name     = var.db_name
    db_user     = var.db_username
    db_password = var.db_password
    redis_host  = aws_elasticache_cluster.redis.cache_nodes[0].address
    redis_port  = 6379
    project     = var.project_name
  }))

  tags = {
    Name = "${var.project_name}-app-server"
  }

  depends_on = [
    aws_db_instance.postgres,
    aws_elasticache_cluster.redis,
  ]
}

# Elastic IP for stable public access
resource "aws_eip" "app_server" {
  instance = aws_instance.app_server.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }
}

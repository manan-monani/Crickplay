#!/bin/bash
# ============================================
# Crickplay EC2 Bootstrap Script
# Installs Docker, Docker Compose, Python, and configures the environment
# ============================================

set -euo pipefail

exec > /var/log/crickplay-setup.log 2>&1

echo "=== Crickplay EC2 Setup Starting ==="

# Update system
apt-get update -y
apt-get upgrade -y

# Install essential packages
apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  git \
  unzip \
  jq \
  htop \
  python3.11 \
  python3.11-venv \
  python3-pip \
  postgresql-client

# ============================================
# Install Docker
# ============================================
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Enable and start Docker
systemctl enable docker
systemctl start docker

# ============================================
# Install AWS CLI v2
# ============================================
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip -q /tmp/awscliv2.zip -d /tmp/
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscliv2.zip

# ============================================
# Setup project directory
# ============================================
PROJECT_DIR="/opt/${project}"
mkdir -p $PROJECT_DIR
chown ubuntu:ubuntu $PROJECT_DIR

# ============================================
# Create cloud Docker Compose
# (Kafka, Zookeeper, Kafka-UI, MLflow only — Postgres/Redis are managed)
# ============================================
cat > $PROJECT_DIR/docker-compose.cloud.yml << 'COMPOSE_EOF'
# Crickplay Cloud Stack
# Postgres & Redis are managed via AWS RDS/ElastiCache

services:
  # Zookeeper (Kafka dependency)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: crickplay-zookeeper
    restart: unless-stopped
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  # Apache Kafka
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: crickplay-kafka
    restart: unless-stopped
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Kafka UI
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: crickplay-kafka-ui
    restart: unless-stopped
    depends_on:
      - kafka
    ports:
      - "8081:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: crickplay-cloud
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181

  # MLflow Tracking Server
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.10.0
    container_name: crickplay-mlflow
    restart: unless-stopped
    ports:
      - "5001:5001"
    environment:
      MLFLOW_BACKEND_STORE_URI: "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/mlflow"
      MLFLOW_DEFAULT_ARTIFACT_ROOT: /mlflow/artifacts
    volumes:
      - mlflow_data:/mlflow/artifacts
    command: >
      mlflow server
      --host 0.0.0.0
      --port 5001
      --backend-store-uri "postgresql://${db_user}:${db_password}@${db_host}:${db_port}/mlflow"
      --default-artifact-root /mlflow/artifacts

volumes:
  mlflow_data:

networks:
  default:
    name: crickplay-network
COMPOSE_EOF

chown ubuntu:ubuntu $PROJECT_DIR/docker-compose.cloud.yml

# ============================================
# Create .env file with cloud endpoints
# ============================================
cat > $PROJECT_DIR/.env << ENV_EOF
# Auto-generated cloud environment
APP_ENV=development
DEBUG=true

# Database (AWS RDS)
DATABASE_URL=postgresql+asyncpg://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}

# Redis (AWS ElastiCache)
REDIS_URL=redis://${redis_host}:${redis_port}

# Kafka (local Docker on EC2)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Auth
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5001
ENV_EOF

chown ubuntu:ubuntu $PROJECT_DIR/.env
chmod 600 $PROJECT_DIR/.env

# ============================================
# Create mlflow database
# ============================================
PGPASSWORD="${db_password}" psql -h "${db_host}" -p "${db_port}" -U "${db_user}" -d postgres -c "CREATE DATABASE mlflow;" 2>/dev/null || echo "mlflow DB may already exist"

# ============================================
# Start Docker Compose services
# ============================================
cd $PROJECT_DIR
sudo -u ubuntu docker compose -f docker-compose.cloud.yml up -d

# ============================================
# Create a helper script for managing the app
# ============================================
cat > /usr/local/bin/crickplay << 'HELPER_EOF'
#!/bin/bash
case "$1" in
  up)
    cd /opt/crickplay && docker compose -f docker-compose.cloud.yml up -d
    ;;
  down)
    cd /opt/crickplay && docker compose -f docker-compose.cloud.yml down
    ;;
  logs)
    cd /opt/crickplay && docker compose -f docker-compose.cloud.yml logs -f
    ;;
  status)
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
  env)
    cat /opt/crickplay/.env
    ;;
  *)
    echo "Usage: crickplay {up|down|logs|status|env}"
    ;;
esac
HELPER_EOF
chmod +x /usr/local/bin/crickplay

echo "=== Crickplay EC2 Setup Complete ==="
echo "Services: Kafka, Zookeeper, Kafka-UI, MLflow"
echo "Managed: PostgreSQL (RDS), Redis (ElastiCache)"

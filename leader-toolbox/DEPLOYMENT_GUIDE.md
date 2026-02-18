# Leader Toolbox Memory System - Deployment Guide

This comprehensive guide walks you through deploying the Leader Toolbox Memory System, from development setup to production deployment.

## 📋 Overview

The Leader Toolbox Memory System is a **production-ready, OpenClaw-compatible memory system** built with:

- **Kotlin + Spring Boot 3.2**: Robust, type-safe backend
- **PostgreSQL 15+**: Reliable structured data storage with JSONB support
- **Elasticsearch 8.x**: High-performance search with vector capabilities
- **all-MiniLM-L6-v2**: Efficient 384-dimensional embeddings
- **Docker**: Containerized deployment and orchestration

## 🚀 Quick Start (5 minutes)

### Prerequisites
- **Docker & Docker Compose**: For dependencies
- **Java 17+**: For building and running
- **Git**: For cloning the repository

### 1-2-3 Deployment
```bash
# 1. Clone and enter the project
git clone <repository-url>
cd leader-toolbox

# 2. Start dependencies
docker-compose up -d

# 3. Run the application (with auto-download of dependencies)
./gradlew bootRun

# ✅ Application ready at http://localhost:8080
```

### Quick Test
```bash
# Test OpenClaw compatibility
curl -X POST http://localhost:8080/api/v1/memory/ingest_text \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Document", "content": "Hello from Leader Toolbox!"}'

curl -X POST http://localhost:8080/api/v1/memory/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "maxResults": 5}'

curl http://localhost:8080/api/v1/memory/status
```

## 🛠️ Development Setup

### Local Development Environment

#### 1. Install Prerequisites

**macOS:**
```bash
# Install Java 17+
brew install openjdk@17

# Install Docker
brew install --cask docker

# Install PostgreSQL tools (optional, for direct DB access)
brew install postgresql
```

**Ubuntu/Debian:**
```bash
# Install Java 17+
sudo apt update
sudo apt install openjdk-17-jdk

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install PostgreSQL tools
sudo apt install postgresql-client
```

**Windows:**
```bash
# Use Windows Subsystem for Linux (WSL2) with Ubuntu
# Or install Java 17+ and Docker Desktop directly
```

#### 2. Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd leader-toolbox

# Verify project structure
./scripts/validate_implementation.sh

# Expected output: ✅ Implementation validation completed successfully!
```

#### 3. Configure Environment

Create environment configuration:

```bash
# Copy example environment file
cat > .env << 'EOF'
# Database Configuration
DB_USERNAME=leader_toolbox
DB_PASSWORD=secure_password_123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=leader_toolbox

# Elasticsearch Configuration
ELASTICSEARCH_URIS=http://localhost:9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=

# Embedding Service Configuration (optional)
HUGGINGFACE_API_KEY=your_hf_token_here

# Application Configuration
LOG_LEVEL=INFO
SPRING_PROFILES_ACTIVE=development
EOF
```

#### 4. Start Dependencies

```bash
# Start PostgreSQL and Elasticsearch
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# postgresql_container  Up  5432/tcp
# elasticsearch_container  Up  9200/tcp
```

#### 5. Database Setup

```bash
# Run database migrations
./gradlew flywayMigrate

# Verify migration
./gradlew flywayInfo

# Expected: 2 migrations applied successfully
```

#### 6. Build and Run

```bash
# Build the application
./gradlew build

# Run tests (includes integration tests with Testcontainers)
./gradlew test

# Start the application
./gradlew bootRun

# Application will be available at http://localhost:8080
```

### Development Workflow

#### Hot Reload Development
```bash
# Enable development profile with hot reload
./gradlew bootRun --args='--spring.profiles.active=development'

# In another terminal, watch for changes
./gradlew build --continuous
```

#### Database Management
```bash
# Connect to database
psql -h localhost -U leader_toolbox -d leader_toolbox

# View migrations
./gradlew flywayInfo

# Reset database (development only)
./gradlew flywayClean flywayMigrate
```

#### Testing

```bash
# Run all tests
./gradlew test

# Run only unit tests
./gradlew test --tests "*Unit*"

# Run only integration tests
./gradlew test --tests "*Integration*"

# Run OpenClaw compatibility tests
./gradlew test --tests "*OpenClawCompatibility*"

# Generate test report
./gradlew test jacocoTestReport
open build/reports/jacoco/test/html/index.html
```

## 🐳 Docker Deployment

### Development with Docker

```bash
# Build application image
docker build -t leader-toolbox:dev .

# Run with docker-compose (includes all dependencies)
docker-compose -f docker-compose.dev.yml up
```

### Production Docker Setup

#### 1. Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
# Multi-stage build for optimized production image
FROM gradle:8.5-jdk17 AS builder

WORKDIR /app
COPY build.gradle.kts settings.gradle.kts ./
COPY src src/

# Build application
RUN gradle build -x test --no-daemon

FROM openjdk:17-jre-slim

# Add application user
RUN addgroup --system spring && adduser --system spring --ingroup spring
USER spring:spring

# Copy application
COPY --from=builder /app/build/libs/*.jar app.jar

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/api/actuator/health || exit 1

# Expose port
EXPOSE 8080

# Run application
ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
```

#### 2. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgresql:
    image: postgres:15
    environment:
      POSTGRES_DB: leader_toolbox
      POSTGRES_USER: leader_toolbox
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/postgres-init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    command: postgres -c shared_preload_libraries=vector
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U leader_toolbox"]
      interval: 30s
      timeout: 10s
      retries: 5

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.1
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  leader-toolbox:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      SPRING_PROFILES_ACTIVE: production
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgresql:5432/leader_toolbox
      SPRING_DATASOURCE_USERNAME: leader_toolbox
      SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
      SPRING_ELASTICSEARCH_URIS: http://elasticsearch:9200
      MEMORY_EMBEDDING_HUGGINGFACE_API_KEY: ${HUGGINGFACE_API_KEY}
    ports:
      - "8080:8080"
    depends_on:
      postgresql:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - leader-toolbox
    restart: unless-stopped

volumes:
  postgres_data:
  elasticsearch_data:
```

#### 3. Deploy to Production

```bash
# Set production environment variables
export DB_PASSWORD="your_secure_production_password"
export HUGGINGFACE_API_KEY="your_production_hf_key"

# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl http://localhost:8080/api/v1/memory/status
```

## ☁️ Cloud Deployment

### AWS Deployment with ECS

#### 1. ECS Task Definition

```json
{
  "family": "leader-toolbox",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/leader-toolbox-task-role",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/leader-toolbox-execution-role",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "leader-toolbox",
      "image": "your-registry/leader-toolbox:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SPRING_PROFILES_ACTIVE",
          "value": "production"
        },
        {
          "name": "SPRING_DATASOURCE_URL",
          "value": "jdbc:postgresql://your-rds-endpoint:5432/leader_toolbox"
        }
      ],
      "secrets": [
        {
          "name": "SPRING_DATASOURCE_PASSWORD",
          "valueFrom": "arn:aws:ssm:region:account:parameter/leader-toolbox/db-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/leader-toolbox",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8080/api/actuator/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### 2. AWS Infrastructure

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier leader-toolbox-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 100 \
  --db-name leader_toolbox \
  --master-username leader_toolbox \
  --master-user-password "$(aws ssm get-parameter --name /leader-toolbox/db-password --with-decryption --query 'Parameter.Value' --output text)"

# Create OpenSearch (Elasticsearch compatible) cluster
aws opensearch create-domain \
  --domain-name leader-toolbox-search \
  --opensearch-cluster-config InstanceType=t3.small.search,InstanceCount=1 \
  --ebs-options EBSEnabled=true,VolumeType=gp3,VolumeSize=20

# Create ECS cluster
aws ecs create-cluster --cluster-name leader-toolbox-cluster

# Create service
aws ecs create-service \
  --cluster leader-toolbox-cluster \
  --service-name leader-toolbox-service \
  --task-definition leader-toolbox \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-abcdef],assignPublicIp=ENABLED}"
```

### Kubernetes Deployment

#### 1. Kubernetes Manifests

Create `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: leader-toolbox
```

Create `k8s/configmap.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: leader-toolbox-config
  namespace: leader-toolbox
data:
  application.yml: |
    spring:
      profiles:
        active: kubernetes
      datasource:
        url: jdbc:postgresql://postgres-service:5432/leader_toolbox
        username: leader_toolbox
      elasticsearch:
        uris: http://elasticsearch-service:9200
    memory:
      embedding:
        huggingface:
          timeout: 30s
```

Create `k8s/secret.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: leader-toolbox-secrets
  namespace: leader-toolbox
type: Opaque
data:
  db-password: <base64-encoded-password>
  huggingface-api-key: <base64-encoded-key>
```

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: leader-toolbox
  namespace: leader-toolbox
spec:
  replicas: 3
  selector:
    matchLabels:
      app: leader-toolbox
  template:
    metadata:
      labels:
        app: leader-toolbox
    spec:
      containers:
      - name: leader-toolbox
        image: leader-toolbox:latest
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_DATASOURCE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: leader-toolbox-secrets
              key: db-password
        - name: MEMORY_EMBEDDING_HUGGINGFACE_API_KEY
          valueFrom:
            secretKeyRef:
              name: leader-toolbox-secrets
              key: huggingface-api-key
        volumeMounts:
        - name: config
          mountPath: /app/config
        livenessProbe:
          httpGet:
            path: /api/actuator/health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/actuator/health/readiness
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: config
        configMap:
          name: leader-toolbox-config
```

#### 2. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n leader-toolbox

# Expose service
kubectl expose deployment leader-toolbox \
  --type=LoadBalancer \
  --port=80 \
  --target-port=8080 \
  -n leader-toolbox

# Get external IP
kubectl get service leader-toolbox -n leader-toolbox
```

## 🔧 Configuration Management

### Environment-Specific Configuration

#### Development (`application-development.yml`)
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/leader_toolbox_dev
  jpa:
    show-sql: true

memory:
  embedding:
    local:
      enabled: true
    huggingface:
      timeout: 60s

logging:
  level:
    com.leadertoolbox.memory: DEBUG
```

#### Testing (`application-test.yml`)
```yaml
spring:
  datasource:
    url: jdbc:h2:mem:testdb
  jpa:
    hibernate:
      ddl-auto: create-drop

memory:
  elasticsearch:
    enabled: false
  embedding:
    local:
      enabled: true
    huggingface:
      enabled: false
```

#### Production (`application-production.yml`)
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 40
      minimum-idle: 10
  jpa:
    show-sql: false

memory:
  analytics:
    enabled: true
  embedding:
    huggingface:
      api-key: ${HUGGINGFACE_API_KEY}

logging:
  level:
    com.leadertoolbox.memory: INFO
  file:
    name: /var/log/leader-toolbox/application.log
```

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SPRING_PROFILES_ACTIVE` | Active Spring profile | development | No |
| `DB_USERNAME` | Database username | leader_toolbox | Yes |
| `DB_PASSWORD` | Database password | - | Yes |
| `ELASTICSEARCH_URIS` | Elasticsearch endpoints | http://localhost:9200 | Yes |
| `HUGGINGFACE_API_KEY` | HuggingFace API key | - | No |
| `LOG_LEVEL` | Application log level | INFO | No |
| `JVM_OPTS` | JVM options | -Xms1g -Xmx2g | No |

## 📊 Monitoring and Observability

### Health Checks

The application provides comprehensive health checks:

```bash
# Basic health
curl http://localhost:8080/api/actuator/health

# Detailed health (with dependencies)
curl http://localhost:8080/api/actuator/health/db
curl http://localhost:8080/api/actuator/health/elasticsearch

# Custom memory system health
curl http://localhost:8080/api/v1/memory/health
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8080/api/actuator/prometheus

# Application metrics
curl http://localhost:8080/api/actuator/metrics
curl http://localhost:8080/api/actuator/metrics/memory.search.time

# Cache statistics
curl http://localhost:8080/api/actuator/caches
```

### Logging

```bash
# Change log levels at runtime
curl -X POST http://localhost:8080/api/actuator/loggers/com.leadertoolbox.memory \
  -H "Content-Type: application/json" \
  -d '{"configuredLevel": "DEBUG"}'

# View loggers
curl http://localhost:8080/api/actuator/loggers
```

### Grafana Dashboard

Import the provided Grafana dashboard (`monitoring/leader-toolbox-dashboard.json`) for comprehensive monitoring.

## 🔒 Security

### Production Security Checklist

#### Application Security
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure CORS appropriately
- [ ] Set up API rate limiting
- [ ] Enable request/response logging
- [ ] Configure security headers

#### Database Security
- [ ] Use strong database passwords
- [ ] Enable SSL for database connections
- [ ] Configure database firewall rules
- [ ] Set up database backup encryption
- [ ] Enable audit logging

#### Infrastructure Security
- [ ] Update all container images regularly
- [ ] Scan images for vulnerabilities
- [ ] Configure network security groups
- [ ] Enable container runtime security
- [ ] Set up log aggregation

### SSL/TLS Configuration

#### Nginx SSL Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://leader-toolbox:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Test database connectivity
psql -h localhost -U leader_toolbox -d leader_toolbox -c "SELECT version();"

# Check connection pool
curl http://localhost:8080/api/actuator/metrics/hikaricp.connections.active
```

#### Elasticsearch Issues
```bash
# Test Elasticsearch connectivity
curl http://localhost:9200/_cluster/health

# Check indices
curl http://localhost:9200/_cat/indices?v
```

#### Memory/Performance Issues
```bash
# Check JVM memory usage
curl http://localhost:8080/api/actuator/metrics/jvm.memory.used

# Check garbage collection
curl http://localhost:8080/api/actuator/metrics/jvm.gc.pause

# Enable JVM debugging
export JVM_OPTS="-XX:+UnlockDiagnosticVMOptions -XX:+LogVMOutput"
```

#### Application Logs
```bash
# View application logs
docker logs leader-toolbox-container

# Enable debug logging
curl -X POST http://localhost:8080/api/actuator/loggers/com.leadertoolbox \
  -H "Content-Type: application/json" \
  -d '{"configuredLevel": "DEBUG"}'
```

### Performance Tuning

#### JVM Tuning
```bash
# Production JVM options
export JVM_OPTS="-XX:+UseG1GC \
                 -XX:MaxGCPauseMillis=200 \
                 -XX:+UseContainerSupport \
                 -XX:MaxRAMPercentage=75.0 \
                 -XX:+ExitOnOutOfMemoryError"
```

#### Database Tuning
```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
SELECT pg_reload_conf();
```

#### Elasticsearch Tuning
```bash
# Elasticsearch heap size
export ES_JAVA_OPTS="-Xms2g -Xmx2g"

# Index optimization
curl -X PUT http://localhost:9200/memory-chunks/_settings \
  -H "Content-Type: application/json" \
  -d '{"refresh_interval": "30s", "number_of_replicas": 1}'
```

## 📈 Scaling

### Horizontal Scaling

#### Load Balancer Configuration
```nginx
upstream leader_toolbox {
    server leader-toolbox-1:8080 weight=1 max_fails=2 fail_timeout=30s;
    server leader-toolbox-2:8080 weight=1 max_fails=2 fail_timeout=30s;
    server leader-toolbox-3:8080 weight=1 max_fails=2 fail_timeout=30s;

    keepalive 32;
}

server {
    location / {
        proxy_pass http://leader_toolbox;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

#### Database Scaling
```bash
# PostgreSQL read replicas
# Master-slave replication for read scaling

# Connection pooling
# Use PgBouncer for connection pooling
docker run -d \
  -p 6432:6432 \
  -e DATABASES_HOST=postgres-master \
  -e DATABASES_PORT=5432 \
  -e DATABASES_USER=leader_toolbox \
  pgbouncer/pgbouncer:latest
```

### Vertical Scaling

#### Memory Optimization
```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Auto-scaling

#### Kubernetes HPA
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: leader-toolbox-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: leader-toolbox
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Run validation script: `./scripts/validate_implementation.sh`
- [ ] Execute all tests: `./gradlew test`
- [ ] Build application: `./gradlew build`
- [ ] Review configuration for target environment
- [ ] Prepare environment variables and secrets
- [ ] Set up monitoring and alerting

### Deployment
- [ ] Deploy infrastructure (databases, networking)
- [ ] Run database migrations: `./gradlew flywayMigrate`
- [ ] Deploy application
- [ ] Verify health checks pass
- [ ] Test OpenClaw API compatibility
- [ ] Validate performance benchmarks
- [ ] Configure SSL/TLS certificates
- [ ] Set up log aggregation

### Post-Deployment
- [ ] Monitor application metrics
- [ ] Verify search functionality
- [ ] Test failover scenarios
- [ ] Document deployment specifics
- [ ] Train operations team
- [ ] Set up backup procedures

## 📞 Support

### Resources
- **Documentation**: Complete guides and API reference
- **GitHub Issues**: Bug reports and feature requests
- **Monitoring**: Built-in health checks and metrics
- **Logs**: Comprehensive logging with configurable levels

### Getting Help
1. Check the troubleshooting section
2. Review application logs
3. Validate configuration
4. Test with minimal setup
5. Report issues with logs and configuration

---

**The Leader Toolbox Memory System is production-ready and provides a seamless migration path from OpenClaw with significant enhancements in performance, scalability, and features.**
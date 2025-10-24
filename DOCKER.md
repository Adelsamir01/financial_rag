# Docker Deployment Guide

This guide explains how to package and deploy the RAG system using Docker.

## 🐳 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### 1. Build the Docker Image

```bash
# Using the build script (recommended)
./scripts/build.sh

# Or manually
docker build -t rag-system:latest .
```

### 2. Run with Docker Compose

```bash
# Start the application
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop the application
docker-compose down
```

### 3. Access the Application

- Open http://localhost:8501 in your browser
- The application will be running in a containerized environment

## 📁 Docker Files Structure

```
rag_reports/
├── Dockerfile              # Main Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Files to ignore during build
├── scripts/
│   ├── build.sh           # Build Docker image
│   ├── run.sh             # Run with Docker Compose
│   └── ingest.sh          # Ingest documents in container
└── data/                   # PDF files (mounted as volume)
```

## 🔧 Docker Configuration

### Dockerfile Features

- **Base Image**: Python 3.11 slim for efficiency
- **Security**: Non-root user for security
- **Dependencies**: All Python packages pre-installed
- **Health Check**: Built-in health monitoring
- **Port**: Exposes port 8501 for Streamlit

### Docker Compose Features

- **Volume Mounting**: 
  - `./data` → `/app/data` (PDF files)
  - `./.env` → `/app/.env` (API keys)
  - `./faiss_index.bin` → `/app/faiss_index.bin` (index file)
  - `./meta.json` → `/app/meta.json` (metadata)
- **Environment Variables**: Streamlit configuration
- **Restart Policy**: Automatic restart on failure
- **Health Checks**: Container health monitoring

## 🚀 Usage Scenarios

### Development

```bash
# Build and run for development
docker-compose up --build

# View logs
docker-compose logs -f

# Stop and clean up
docker-compose down
```

### Production

```bash
# Build production image
docker build -t rag-system:production .

# Run with production settings
docker run -d \
  --name rag-system \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  -e STREAMLIT_SERVER_HEADLESS=true \
  rag-system:production
```

### Document Ingestion

```bash
# Ingest documents inside container
docker-compose exec rag-system python ingest.py

# Or use the ingest script
docker-compose exec rag-system ./scripts/ingest.sh
```

## 🛠️ Customization

### Environment Variables

Create a `.env` file with:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Volume Configuration

The system uses several volumes:

- **Data Volume**: `./data` - Contains PDF files
- **Environment Volume**: `./.env` - API keys and configuration
- **Index Volumes**: `./faiss_index.bin` and `./meta.json` - Vector index and metadata

### Port Configuration

Default port is 8501. To change:

```yaml
# In docker-compose.yml
ports:
  - "8080:8501"  # Map host port 8080 to container port 8501
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 8501
   lsof -i :8501
   
   # Kill the process or use different port
   docker-compose up --build -p 8502:8501
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Missing Environment Variables**
   ```bash
   # Check if .env file exists
   ls -la .env
   
   # Create .env file from template
   cp .env.example .env
   ```

4. **Container Won't Start**
   ```bash
   # Check container logs
   docker-compose logs rag-system
   
   # Check container status
   docker-compose ps
   ```

### Debugging

```bash
# Run container in interactive mode
docker run -it --rm rag-system:latest /bin/bash

# Check container health
docker-compose exec rag-system curl -f http://localhost:8501/_stcore/health

# View detailed logs
docker-compose logs --tail=100 -f rag-system
```

## 📊 Performance Optimization

### Resource Limits

```yaml
# In docker-compose.yml
services:
  rag-system:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### Multi-stage Build (Advanced)

For production, consider a multi-stage build:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
# ... rest of configuration
```

## 🔒 Security Considerations

### Production Security

1. **Secrets Management**: Use Docker secrets or external secret management
2. **Network Security**: Use Docker networks for isolation
3. **User Permissions**: Run as non-root user (already configured)
4. **Resource Limits**: Set appropriate CPU and memory limits
5. **Health Checks**: Monitor container health

### Example Production Setup

```yaml
version: '3.8'

services:
  rag-system:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - rag-data:/app/data
      - rag-index:/app
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_key
    secrets:
      - openai_key
    networks:
      - rag-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

volumes:
  rag-data:
  rag-index:

secrets:
  openai_key:
    external: true

networks:
  rag-network:
    driver: bridge
```

## 🚀 Deployment Options

### Local Development
- Use `docker-compose up` for local development
- Mount local directories for live code changes

### Cloud Deployment
- **AWS**: Use ECS, EKS, or EC2 with Docker
- **Google Cloud**: Use Cloud Run or GKE
- **Azure**: Use Container Instances or AKS
- **DigitalOcean**: Use App Platform or Droplets

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: Build and Deploy
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t rag-system:${{ github.sha }} .
      - name: Deploy to production
        run: docker-compose -f docker-compose.prod.yml up -d
```

## 📈 Monitoring and Logging

### Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker-compose ps

# Manual health check
curl -f http://localhost:8501/_stcore/health
```

### Logging

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f rag-system

# Follow logs with timestamps
docker-compose logs -f -t rag-system
```

### Monitoring

Consider adding monitoring tools:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation
- **Docker Stats**: Resource monitoring

## 🎯 Best Practices

1. **Use .dockerignore**: Exclude unnecessary files
2. **Multi-stage builds**: Reduce image size
3. **Health checks**: Monitor application health
4. **Resource limits**: Prevent resource exhaustion
5. **Security scanning**: Regular vulnerability scans
6. **Backup volumes**: Regular data backups
7. **Update strategy**: Rolling updates for zero downtime

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Streamlit Deployment](https://docs.streamlit.io/deploy)
- [OpenAI API Documentation](https://platform.openai.com/docs)


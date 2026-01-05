#!/bin/bash

# HealthDB Deployment Script
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)

echo "🚀 HealthDB Deployment Script"
echo "================================"
echo "Environment: $ENVIRONMENT"
echo "Project Dir: $PROJECT_DIR"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check .env file
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_warn ".env file not found. Creating from .env.example..."
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            log_warn "Please edit .env with your configuration before running again."
            exit 1
        else
            log_error ".env.example not found. Please create a .env file."
            exit 1
        fi
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Build the application
build() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_DIR"
    docker-compose build --no-cache
    
    log_info "Build completed ✓"
}

# Deploy to production
deploy_production() {
    log_info "Deploying to production..."
    
    cd "$PROJECT_DIR"
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Pull latest images and start
    docker-compose --profile production up -d
    
    # Wait for health checks
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    if curl -sf http://localhost:8000/api/health > /dev/null; then
        log_info "API is healthy ✓"
    else
        log_error "API health check failed"
        docker-compose logs api
        exit 1
    fi
    
    log_info "Production deployment completed ✓"
}

# Deploy to development
deploy_development() {
    log_info "Deploying to development..."
    
    cd "$PROJECT_DIR"
    
    # Start services in development mode
    docker-compose up -d db redis
    
    # Wait for database
    log_info "Waiting for database..."
    sleep 5
    
    # Run API in development mode
    docker-compose up -d api
    
    log_info "Development deployment completed ✓"
    log_info "API available at: http://localhost:8000"
    log_info "API docs at: http://localhost:8000/api/docs"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    docker-compose exec api python -c "
from database import init_database
init_database()
print('Migrations completed successfully')
"
    
    log_info "Migrations completed ✓"
}

# Show logs
show_logs() {
    docker-compose logs -f
}

# Main execution
main() {
    check_prerequisites
    
    case $ENVIRONMENT in
        production)
            build
            deploy_production
            run_migrations
            ;;
        development)
            deploy_development
            ;;
        build)
            build
            ;;
        logs)
            show_logs
            ;;
        *)
            echo "Usage: $0 [production|development|build|logs]"
            exit 1
            ;;
    esac
    
    echo ""
    echo "================================"
    echo "🎉 Deployment completed!"
    echo "================================"
}

main


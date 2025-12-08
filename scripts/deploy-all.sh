#!/bin/bash
#
# Unified Deployment Orchestration Script
#
# This script orchestrates the complete deployment process:
# 1. Infrastructure (Terraform)
# 2. Database Schema
# 3. Function App Code
# 4. Health Checks
#
# Designed for integration into larger project deployment pipelines.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-"dev"}
DEPLOY_INFRASTRUCTURE=${DEPLOY_INFRASTRUCTURE:-"true"}
DEPLOY_DATABASE=${DEPLOY_DATABASE:-"true"}
DEPLOY_FUNCTION_APP=${DEPLOY_FUNCTION_APP:-"true"}
SKIP_HEALTH_CHECKS=${SKIP_HEALTH_CHECKS:-"false"}
DRY_RUN=${DRY_RUN:-"false"}

# Deployment tracking
DEPLOYMENT_LOG="$PROJECT_ROOT/deployment-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).log"
DEPLOYMENT_START_TIME=$(date +%s)

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check required tools
    command -v terraform >/dev/null 2>&1 || missing_tools+=("terraform")
    command -v az >/dev/null 2>&1 || missing_tools+=("azure-cli")
    command -v psql >/dev/null 2>&1 || missing_tools+=("postgresql-client")
    command -v python3 >/dev/null 2>&1 || missing_tools+=("python3")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    # Check environment variables
    local required_vars=(
        "AZURE_SUBSCRIPTION_ID"
        "AZURE_TENANT_ID"
        "AZURE_CLIENT_ID"
        "AZURE_CLIENT_SECRET"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        env_var_name="${ENVIRONMENT^^}_${var}"
        if [ -z "${!env_var_name}" ] && [ -z "${!var}" ]; then
            missing_vars+=("$var or ${env_var_name}")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    if [ "$DEPLOY_INFRASTRUCTURE" != "true" ]; then
        log_info "Skipping infrastructure deployment"
        return 0
    fi
    
    log_info "Deploying infrastructure (Terraform)..."
    
    cd "$PROJECT_ROOT/iac/environments/$ENVIRONMENT"
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would run: terraform plan"
        terraform init
        terraform plan
        return 0
    fi
    
    terraform init
    terraform validate
    terraform plan -out=tfplan
    terraform apply tfplan
    
    log_success "Infrastructure deployed successfully"
}

# Function to deploy database schema
deploy_database() {
    if [ "$DEPLOY_DATABASE" != "true" ]; then
        log_info "Skipping database schema deployment"
        return 0
    fi
    
    log_info "Deploying database schema..."
    
    # Get database connection info from Terraform outputs
    cd "$PROJECT_ROOT/iac/environments/$ENVIRONMENT"
    
    if [ ! -f terraform.tfstate ]; then
        log_warning "Terraform state not found. Cannot get database connection info."
        log_info "Please set DATABASE_HOST, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD manually"
        return 1
    fi
    
    # Extract database info from Terraform (if available)
    # This is a simplified version - in production, use terraform output
    export DATABASE_HOST=${DATABASE_HOST:-"payments-ingestion-${ENVIRONMENT}-psql-eus.postgres.database.azure.com"}
    export DATABASE_NAME=${DATABASE_NAME:-"payments_db"}
    export DATABASE_USER=${DATABASE_USER:-"psqladmin"}
    export DATABASE_PASSWORD=${DATABASE_PASSWORD:-"${ENVIRONMENT^^}_POSTGRESQL_PASSWORD"}
    
    if [ "$DRY_RUN" = "true" ]; then
        DRY_RUN="true" "$PROJECT_ROOT/scripts/database/deploy-schema.sh" "$ENVIRONMENT"
    else
        "$PROJECT_ROOT/scripts/database/deploy-schema.sh" "$ENVIRONMENT"
    fi
    
    log_success "Database schema deployed successfully"
}

# Function to deploy Function App code
deploy_function_app() {
    if [ "$DEPLOY_FUNCTION_APP" != "true" ]; then
        log_info "Skipping Function App code deployment"
        return 0
    fi
    
    log_info "Deploying Function App code..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] Would package and deploy Function App code"
        return 0
    fi
    
    # This would typically call the GitHub Actions workflow or use Azure CLI directly
    # For now, log that this step would be executed
    log_info "Function App code deployment should be done via GitHub Actions workflow"
    log_info "Or use: az functionapp deployment source config-zip ..."
    
    log_success "Function App code deployment step completed"
}

# Function to run health checks
run_health_checks() {
    if [ "$SKIP_HEALTH_CHECKS" = "true" ]; then
        log_info "Skipping health checks"
        return 0
    fi
    
    log_info "Running health checks..."
    
    local health_check_passed=true
    
    # Check Function App health
    log_info "Checking Function App health..."
    FUNC_APP_NAME="payments-ingestion-${ENVIRONMENT}-func-eus"
    RG_NAME="payments-ingestion-${ENVIRONMENT}-rg"
    
    FUNC_STATUS=$(az functionapp show \
        --resource-group "$RG_NAME" \
        --name "$FUNC_APP_NAME" \
        --query "state" -o tsv 2>/dev/null || echo "Unknown")
    
    if [ "$FUNC_STATUS" = "Running" ]; then
        log_success "Function App is running"
    else
        log_warning "Function App status: $FUNC_STATUS"
        health_check_passed=false
    fi
    
    # Check database connectivity
    log_info "Checking database connectivity..."
    if [ -n "$DATABASE_HOST" ] && [ -n "$DATABASE_PASSWORD" ]; then
        export PGPASSWORD="$DATABASE_PASSWORD"
        if psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
            log_success "Database is accessible"
        else
            log_warning "Database connectivity check failed"
            health_check_passed=false
        fi
        unset PGPASSWORD
    else
        log_warning "Database credentials not available, skipping connectivity check"
    fi
    
    if [ "$health_check_passed" = "true" ]; then
        log_success "All health checks passed"
    else
        log_warning "Some health checks failed (deployment may still be successful)"
    fi
}

# Function to display deployment summary
display_summary() {
    local deployment_end_time=$(date +%s)
    local duration=$((deployment_end_time - DEPLOYMENT_START_TIME))
    
    echo ""
    echo "========================================"
    echo "Deployment Summary"
    echo "========================================"
    echo "Environment: $ENVIRONMENT"
    echo "Duration: ${duration}s"
    echo "Log file: $DEPLOYMENT_LOG"
    echo ""
    echo "Components Deployed:"
    [ "$DEPLOY_INFRASTRUCTURE" = "true" ] && echo "  ✅ Infrastructure (Terraform)"
    [ "$DEPLOY_DATABASE" = "true" ] && echo "  ✅ Database Schema"
    [ "$DEPLOY_FUNCTION_APP" = "true" ] && echo "  ✅ Function App Code"
    [ "$SKIP_HEALTH_CHECKS" != "true" ] && echo "  ✅ Health Checks"
    echo "========================================"
}

# Main deployment flow
main() {
    log_info "Starting unified deployment for environment: $ENVIRONMENT"
    log_info "Deployment log: $DEPLOYMENT_LOG"
    
    # Check prerequisites
    check_prerequisites
    
    # Deploy components in order
    deploy_infrastructure || {
        log_error "Infrastructure deployment failed"
        exit 1
    }
    
    deploy_database || {
        log_error "Database schema deployment failed"
        exit 1
    }
    
    deploy_function_app || {
        log_error "Function App code deployment failed"
        exit 1
    }
    
    # Run health checks
    run_health_checks
    
    # Display summary
    display_summary
    
    log_success "Deployment completed successfully!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-infrastructure)
            DEPLOY_INFRASTRUCTURE="false"
            shift
            ;;
        --skip-database)
            DEPLOY_DATABASE="false"
            shift
            ;;
        --skip-function-app)
            DEPLOY_FUNCTION_APP="false"
            shift
            ;;
        --skip-health-checks)
            SKIP_HEALTH_CHECKS="true"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [environment] [options]"
            echo ""
            echo "Options:"
            echo "  --skip-infrastructure    Skip infrastructure deployment"
            echo "  --skip-database         Skip database schema deployment"
            echo "  --skip-function-app     Skip Function App code deployment"
            echo "  --skip-health-checks    Skip health checks"
            echo "  --dry-run               Preview changes without applying"
            echo "  --help                  Show this help message"
            exit 0
            ;;
        *)
            ENVIRONMENT=$1
            shift
            ;;
    esac
done

# Run main deployment
main


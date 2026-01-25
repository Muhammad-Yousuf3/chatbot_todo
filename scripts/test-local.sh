#!/bin/bash
# Local Kubernetes Testing Script for 009-dapr-event-driven
# This script sets up Minikube with Dapr and deploys the application

set -e

echo "=========================================="
echo "Todo Chatbot - Local Kubernetes Testing"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prereqs() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"

    for cmd in docker minikube kubectl helm dapr; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}ERROR: $cmd is not installed${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ $cmd found${NC}"
    done
}

# Start Minikube
start_minikube() {
    echo -e "\n${YELLOW}Starting Minikube...${NC}"

    if minikube status | grep -q "Running"; then
        echo -e "${GREEN}Minikube already running${NC}"
    else
        minikube start --cpus=4 --memory=8192 --driver=docker
    fi

    # Point docker to minikube
    eval $(minikube docker-env)
    echo -e "${GREEN}✓ Minikube started and docker configured${NC}"
}

# Install Dapr
install_dapr() {
    echo -e "\n${YELLOW}Installing Dapr on Kubernetes...${NC}"

    if dapr status -k 2>/dev/null | grep -q "Running"; then
        echo -e "${GREEN}Dapr already installed${NC}"
    else
        dapr init -k --wait
    fi

    dapr status -k
    echo -e "${GREEN}✓ Dapr installed${NC}"
}

# Build Docker images
build_images() {
    echo -e "\n${YELLOW}Building Docker images...${NC}"

    # Ensure we're using minikube's docker
    eval $(minikube docker-env)

    echo "Building backend..."
    docker build -t todo-backend:local ./backend

    echo "Building scheduler..."
    docker build -t todo-scheduler:local ./scheduler

    if [ -d "./frontend" ]; then
        echo "Building frontend..."
        docker build -t todo-frontend:local ./frontend
    fi

    echo -e "${GREEN}✓ Images built${NC}"
    docker images | grep todo-
}

# Create namespace and secrets
setup_namespace() {
    echo -e "\n${YELLOW}Setting up namespace and secrets...${NC}"

    kubectl create namespace todo-chatbot --dry-run=client -o yaml | kubectl apply -f -

    # Check if secrets need to be created
    if ! kubectl get secret backend-secrets -n todo-chatbot &>/dev/null; then
        echo -e "${YELLOW}Creating secrets...${NC}"
        echo "Please provide the following values:"

        read -p "DATABASE_URL (PostgreSQL connection string): " DB_URL
        read -p "JWT_SECRET (min 32 chars): " JWT_SECRET
        read -p "GEMINI_API_KEY: " GEMINI_KEY

        kubectl create secret generic backend-secrets \
            --from-literal=DATABASE_URL="$DB_URL" \
            --from-literal=JWT_SECRET="$JWT_SECRET" \
            --from-literal=GEMINI_API_KEY="$GEMINI_KEY" \
            -n todo-chatbot
    else
        echo -e "${GREEN}Secrets already exist${NC}"
    fi

    echo -e "${GREEN}✓ Namespace and secrets configured${NC}"
}

# Deploy with Helm
deploy_helm() {
    echo -e "\n${YELLOW}Deploying with Helm...${NC}"

    helm upgrade --install todo-chatbot ./helm/todo-chatbot \
        -f ./helm/todo-chatbot/values-local.yaml \
        -n todo-chatbot \
        --wait --timeout 5m

    echo -e "${GREEN}✓ Helm deployment complete${NC}"
}

# Wait for pods
wait_for_pods() {
    echo -e "\n${YELLOW}Waiting for pods to be ready...${NC}"

    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=todo-chatbot -n todo-chatbot --timeout=300s || true

    echo -e "\n${YELLOW}Pod status:${NC}"
    kubectl get pods -n todo-chatbot
}

# Verify Dapr components
verify_dapr() {
    echo -e "\n${YELLOW}Verifying Dapr components...${NC}"
    dapr components -n todo-chatbot
}

# Run tests
run_tests() {
    echo -e "\n${YELLOW}Running integration tests...${NC}"

    # Get service URLs
    MINIKUBE_IP=$(minikube ip)

    echo -e "\n${YELLOW}Testing Backend health...${NC}"
    kubectl port-forward svc/todo-backend-svc 8000:8000 -n todo-chatbot &
    PF_PID=$!
    sleep 3

    curl -s http://localhost:8000/health | jq .
    curl -s http://localhost:8000/health/dapr | jq .

    echo -e "\n${YELLOW}Testing Scheduler health...${NC}"
    kubectl port-forward svc/scheduler-svc 8001:8001 -n todo-chatbot &
    PF_PID2=$!
    sleep 3

    curl -s http://localhost:8001/health | jq .
    curl -s http://localhost:8001/health/dapr | jq .

    # Cleanup port forwards
    kill $PF_PID $PF_PID2 2>/dev/null || true

    echo -e "${GREEN}✓ Health checks passed${NC}"
}

# Show access info
show_access() {
    echo -e "\n${GREEN}=========================================="
    echo "Deployment Complete!"
    echo "==========================================${NC}"

    echo -e "\n${YELLOW}Access URLs:${NC}"
    echo "Frontend: $(minikube service todo-frontend-svc -n todo-chatbot --url 2>/dev/null || echo 'Run: minikube service todo-frontend-svc -n todo-chatbot')"

    echo -e "\n${YELLOW}Useful commands:${NC}"
    echo "  View pods:          kubectl get pods -n todo-chatbot"
    echo "  View logs:          kubectl logs -f deployment/todo-backend -n todo-chatbot -c backend"
    echo "  View Dapr logs:     kubectl logs -f deployment/todo-backend -n todo-chatbot -c daprd"
    echo "  Dapr dashboard:     dapr dashboard -k"
    echo "  Redis CLI:          kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli"
    echo "  Port forward API:   kubectl port-forward svc/todo-backend-svc 8000:8000 -n todo-chatbot"

    echo -e "\n${YELLOW}Test event flow:${NC}"
    echo "  1. Create a task with recurrence or reminders via API"
    echo "  2. Check Redis for events: kubectl exec -it deployment/redis -n todo-chatbot -- redis-cli KEYS '*'"
    echo "  3. Check scheduler logs for event processing"
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    helm uninstall todo-chatbot -n todo-chatbot 2>/dev/null || true
    kubectl delete namespace todo-chatbot 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Main execution
main() {
    case "${1:-deploy}" in
        deploy)
            check_prereqs
            start_minikube
            install_dapr
            build_images
            setup_namespace
            deploy_helm
            wait_for_pods
            verify_dapr
            run_tests
            show_access
            ;;
        build)
            eval $(minikube docker-env)
            build_images
            ;;
        test)
            run_tests
            show_access
            ;;
        cleanup)
            cleanup
            ;;
        *)
            echo "Usage: $0 {deploy|build|test|cleanup}"
            exit 1
            ;;
    esac
}

main "$@"

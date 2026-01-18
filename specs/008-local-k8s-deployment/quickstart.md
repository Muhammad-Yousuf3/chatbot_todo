# Quickstart: Phase IV - Local Kubernetes Deployment

**Feature**: 008-local-k8s-deployment
**Date**: 2026-01-18
**Status**: Infrastructure files created, requires Docker daemon for deployment

---

## Prerequisites

Before starting, ensure you have:

| Tool | Version | Check Command |
|------|---------|---------------|
| Docker Desktop | Latest | `docker --version` |
| Minikube | 1.30+ | `minikube version` |
| kubectl | 1.28+ | `kubectl version --client` |
| Helm | 3.12+ | `helm version` |

**Important**: Docker daemon must be running for deployment steps.

---

## Quick Deploy (5 minutes)

### Step 1: Start Docker Daemon

Ensure Docker Desktop is running or start the Docker daemon:

```bash
# On Linux (systemd)
sudo systemctl start docker

# Verify Docker is running
docker ps
```

### Step 2: Start Minikube

```bash
# Start Minikube with sufficient resources
minikube start --cpus=2 --memory=4096

# Verify cluster is running
kubectl cluster-info
```

### Step 3: Configure Docker Environment

```bash
# Point shell's Docker to Minikube's Docker daemon
eval $(minikube docker-env)

# Verify (should show Minikube's images)
docker images
```

### Step 4: Build Docker Images

```bash
# Navigate to project root
cd /path/to/Chatbot_TODO

# Build backend image
docker build -t todo-backend:dev backend/

# Build frontend image (API URL baked in at build time)
docker build -t todo-frontend:dev \
  --build-arg NEXT_PUBLIC_API_URL=http://todo-backend:8000 \
  frontend/

# Verify images are available
docker images | grep todo
```

### Step 5: Deploy with Helm

```bash
# Create namespace
kubectl create namespace todo-chatbot

# Install the chart (provide your secrets)
helm install todo-app ./helm/todo-chatbot \
  --namespace todo-chatbot \
  --set backend.secrets.databaseUrl="YOUR_NEON_DATABASE_URL" \
  --set backend.secrets.jwtSecret="YOUR_JWT_SECRET" \
  --set backend.secrets.geminiApiKey="YOUR_GEMINI_API_KEY"

# Check deployment status
kubectl get pods -n todo-chatbot -w
```

### Step 6: Access the Application

```bash
# Open frontend in browser
minikube service todo-frontend -n todo-chatbot

# Or get the URL manually
minikube service todo-frontend -n todo-chatbot --url
```

---

## Verification Checklist

After deployment, verify:

- [ ] Both pods show `Running` status: `kubectl get pods -n todo-chatbot`
- [ ] Backend health check passes: `kubectl exec -n todo-chatbot deploy/todo-backend -- curl -s localhost:8000/health`
- [ ] Frontend loads in browser
- [ ] Chat functionality works (send a message, get response)
- [ ] Tasks can be created and listed

---

## Common Operations

### View Logs

```bash
# Backend logs
kubectl logs -n todo-chatbot deploy/todo-backend -f

# Frontend logs
kubectl logs -n todo-chatbot deploy/todo-frontend -f
```

### Update Configuration

```bash
# Update Helm values and upgrade
helm upgrade todo-app ./helm/todo-chatbot \
  --namespace todo-chatbot \
  --set backend.config.logLevel=DEBUG
```

### Restart Pods

```bash
# Rollout restart
kubectl rollout restart deployment/todo-backend -n todo-chatbot
kubectl rollout restart deployment/todo-frontend -n todo-chatbot
```

### Uninstall

```bash
# Remove Helm release
helm uninstall todo-app -n todo-chatbot

# Delete namespace (removes all resources)
kubectl delete namespace todo-chatbot

# Stop Minikube (optional)
minikube stop
```

---

## Troubleshooting

### Pod not starting (CrashLoopBackOff)

```bash
# Check pod events
kubectl describe pod -n todo-chatbot -l app=todo-backend

# Check container logs
kubectl logs -n todo-chatbot deploy/todo-backend --previous
```

### Cannot connect to backend from frontend

```bash
# Verify service exists
kubectl get svc -n todo-chatbot

# Test internal DNS
kubectl run -n todo-chatbot test-dns --rm -it --restart=Never \
  --image=busybox -- nslookup todo-backend
```

### Image not found

```bash
# Ensure Docker env is set
eval $(minikube docker-env)

# Rebuild images
docker build -t todo-backend:dev backend/

# Verify imagePullPolicy is IfNotPresent in values.yaml
```

### Database connection failed

```bash
# Check secret is set correctly
kubectl get secret -n todo-chatbot todo-backend-secrets -o yaml

# Verify Minikube can reach external network
kubectl run -n todo-chatbot test-net --rm -it --restart=Never \
  --image=busybox -- wget -qO- https://google.com
```

---

## File Structure Reference

```
Chatbot_TODO/
├── backend/
│   └── Dockerfile          # Backend container definition
├── frontend/
│   └── Dockerfile          # Frontend container definition
└── helm/
    └── todo-chatbot/
        ├── Chart.yaml
        ├── values.yaml
        ├── values-local.yaml
        └── templates/
            ├── _helpers.tpl
            ├── backend/
            │   ├── deployment.yaml
            │   ├── service.yaml
            │   ├── configmap.yaml
            │   └── secret.yaml
            └── frontend/
                ├── deployment.yaml
                ├── service.yaml
                └── configmap.yaml
```

---

## Environment Variables Reference

### Backend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | Neon PostgreSQL connection | `postgresql://user:pass@host/db` |
| JWT_SECRET | Token signing key | `your-secure-secret` |
| GEMINI_API_KEY | Google AI API key | `AIza...` |

### Backend (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| LOG_LEVEL | Logging verbosity | `INFO` |
| FRONTEND_URL | CORS allowed origin | `http://todo-frontend:80` |

### Frontend (Build-time)

| Variable | Description | Default |
|----------|-------------|---------|
| NEXT_PUBLIC_API_URL | Backend API endpoint | `http://todo-backend:8000` |

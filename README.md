# 🔗 LinkSnip — URL Shortener

A production-grade URL shortener built with Python/Flask and Redis, demonstrating a complete **DevOps pipeline** including CI/CD, containerization, Kubernetes orchestration, and Infrastructure as Code.

---

## 🏗️ Architecture

```
User → [Load Balancer] → [Flask App (2 replicas)] → [Redis]
                              ↑
                    Docker / Kubernetes
```

**Stack:** Python · Flask · Redis · Docker · Kubernetes · Terraform · Ansible · GitHub Actions

---

## 📁 Project Structure

```
linksnip/
├── app/
│   ├── app.py                  # Flask application
│   └── requirements.txt
├── tests/
│   └── test_app.py             # Pytest test suite
├── k8s/
│   ├── namespace.yaml          # Kubernetes namespace
│   ├── deployment.yaml         # App deployment (2 replicas)
│   ├── redis-deployment.yaml   # Redis deployment + PVC
│   └── service.yaml            # LoadBalancer + ClusterIP services
├── terraform/
│   ├── main.tf                 # AWS VPC + EC2 + Security Groups
│   ├── variables.tf
│   └── outputs.tf
├── ansible/
│   ├── inventory.ini           # Server inventory
│   └── deploy.yml              # Deployment playbook
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # GitHub Actions pipeline
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Local development setup
└── README.md
```

---

## 🚀 Quick Start (Local Dev)

### Prerequisites
- Docker & Docker Compose
- Python 3.12+

### Run with Docker Compose
```bash
git clone https://github.com/YOUR_USERNAME/linksnip.git
cd linksnip
docker compose up --build
```
App runs at **http://localhost:5000**

### Run Tests
```bash
pip install -r app/requirements.txt
pytest tests/ -v
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

Three automated stages on every push to `main`:

| Stage | What happens |
|-------|-------------|
| **1. Test** | Pytest runs all unit tests |
| **2. Build** | Docker image built & pushed to Docker Hub |
| **3. Deploy** | Kubernetes manifests applied, rollout verified |

### Setup GitHub Secrets
Go to **Settings → Secrets → Actions** and add:

| Secret | Value |
|--------|-------|
| `DOCKER_HUB_USERNAME` | Your Docker Hub username |
| `DOCKER_HUB_TOKEN` | Docker Hub access token |
| `KUBECONFIG` | Base64-encoded kubeconfig (`base64 ~/.kube/config`) |

---

## 🐳 Docker

### Build manually
```bash
docker build -t linksnip .
docker run -p 5000:5000 -e REDIS_HOST=localhost linksnip
```

### Multi-stage build benefits
- Stage 1 (builder): installs all dependencies
- Stage 2 (runtime): copies only what's needed — smaller, secure image
- Runs as **non-root user** (UID 1001)

---

## ☸️ Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n linksnip
kubectl get services -n linksnip

# View logs
kubectl logs -l app=linksnip -n linksnip

# Scale up
kubectl scale deployment linksnip-app --replicas=3 -n linksnip
```

Features:
- **2 replicas** with rolling update strategy (zero downtime)
- **Liveness & Readiness probes** via `/health` endpoint
- **PersistentVolumeClaim** for Redis data durability
- **Resource limits** on all containers

---

## 🏗️ Infrastructure as Code (Terraform)

Provisions AWS infrastructure:
- VPC with public subnet + Internet Gateway
- EC2 instance (Ubuntu 22.04, t3.micro)
- Security Group (SSH, HTTP, HTTPS)
- Elastic IP for stable address

```bash
cd terraform

# Initialize
terraform init

# Preview changes
terraform plan -var="your_ip=$(curl -s ifconfig.me)/32"

# Apply
terraform apply -var="your_ip=$(curl -s ifconfig.me)/32"

# Get server IP
terraform output instance_public_ip
```

---

## 🤖 Ansible Deployment

After Terraform provisions the server:

```bash
cd ansible

# Update inventory.ini with your server IP
# Then run:
ansible-playbook -i inventory.ini deploy.yml
```

The playbook:
1. Installs Docker on the server
2. Copies docker-compose.yml
3. Pulls and starts containers
4. Verifies app health

---

## 🌿 Git Workflow (Branching Strategy)

```
main          ← production, protected branch
  └── develop ← integration branch
        └── feature/add-custom-codes
        └── feature/analytics-dashboard
        └── fix/redis-timeout
```

- **feature branches** → PR to `develop` → review → merge
- **develop** → PR to `main` → triggers full CI/CD pipeline

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `POST` | `/api/shorten` | Shorten a URL |
| `GET` | `/<code>` | Redirect to original URL |
| `GET` | `/api/stats` | Get global statistics |
| `GET` | `/health` | Health check (for K8s probes) |

### Example
```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/very/long/path"}'

# Response:
# {"short_url": "http://localhost:5000/aB3kR9", "code": "aB3kR9"}
```
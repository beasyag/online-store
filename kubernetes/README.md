# MarketFlow Kubernetes Deployment

## Architecture

```
                    Ingress (nginx)
                   /              \
    marketflow.kz                  api.marketflow.kz
         |                              |
  frontend-service (3000)        backend-service (8000)
         |                              |
  Frontend Deployment (x2)       Backend Deployment (x3)
                                        |
                              +---------+---------+
                              |                   |
                       postgres-service      redis-service
                              |                   |
                     PostgreSQL StatefulSet   Redis Deployment
                              |
                         PVC (5Gi)
                              
                       Celery Workers (x2)
```

## Manifests

| File | Description |
|------|-------------|
| `secrets.yaml` | Kubernetes Secret with sensitive data (passwords, API keys) |
| `postgres-statefulset.yaml` | PostgreSQL 16 StatefulSet with PVC (5Gi) |
| `redis-deployment.yaml` | Redis 7 Deployment |
| `backend-deployment.yaml` | Django backend (3 replicas) with health checks |
| `celery-deployment.yaml` | Celery workers (2 replicas) |
| `frontend-deployment.yaml` | Nuxt 3 frontend (2 replicas) with health checks |
| `services.yaml` | ClusterIP/LoadBalancer Services for all components |
| `ingress.yaml` | Nginx Ingress for external access |

## Quick Start

```bash
# 1. Edit secrets (replace CHANGE_ME with real values)
vim kubernetes/secrets.yaml

# 2. Replace image names with your registry
# my-registry/marketflow-backend:latest  -> your-registry/marketflow-backend:latest
# my-registry/marketflow-frontend:latest -> your-registry/marketflow-frontend:latest

# 3. Apply manifests in order
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/postgres-statefulset.yaml
kubectl apply -f kubernetes/redis-deployment.yaml
kubectl apply -f kubernetes/services.yaml
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/celery-deployment.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml
kubectl apply -f kubernetes/ingress.yaml

# 4. Run Django migrations
kubectl exec -it deployment/marketflow-backend -- python manage.py migrate

# 5. Create superuser (optional)
kubectl exec -it deployment/marketflow-backend -- python manage.py createsuperuser
```

## Configuration

### Secrets
Edit `secrets.yaml` before deploying:
- `DB_PASSWORD` — PostgreSQL password
- `DJANGO_SECRET_KEY` — Django secret key (generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `STRIPE_SECRET_KEY` — Stripe API key
- `STRIPE_WEBHOOK_SECRET` — Stripe webhook secret
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google OAuth credentials

### Domain
Update `ALLOWED_HOSTS` in `backend-deployment.yaml` and hosts in `ingress.yaml` to match your domain.

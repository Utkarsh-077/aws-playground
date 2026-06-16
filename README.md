# Super Blog Bros

A full-stack blogging application deployed on AWS, styled after 8-bit Super Mario. Built as a hands-on DevOps playground covering Infrastructure as Code, CI/CD pipelines, containerization, and observability.

---

## Architecture

### AWS (Production)

```
                        ┌─────────────────────────────────────────┐
                        │              GitHub                      │
                        │                                          │
                        │  ┌──────────┐      ┌─────────────────┐  │
                        │  │  app/    │      │ .github/        │  │
                        │  │  app.py  │      │ workflows/      │  │
                        │  │  Dockerfile     │ terraform.yml   │  │
                        │  └──────────┘      └────────┬────────┘  │
                        └───────────────────────────┬─┴───────────┘
                                                    │
                                          git push to main
                                                    │
                                                    ▼
                        ┌─────────────────────────────────────────┐
                        │          GitHub Actions Runner           │
                        │                                          │
                        │  1. docker build + push → ECR           │
                        │  2. terraform init   (reads S3 state)   │
                        │  3. terraform apply  (deploy to AWS)    │
                        └─────────────────┬───────────────────────┘
                                          │
                    ┌─────────────────────┼──────────────────────┐
                    │                     │                       │
                    ▼                     ▼                       ▼
          ┌─────────────────┐   ┌──────────────────┐   ┌─────────────────────┐
          │   S3 Bucket     │   │   ECR Registry   │   │    AWS (Mumbai)     │
          │                 │   │                  │   │                     │
          │  terraform      │   │  super-blog-bros │   │  ┌───────────────┐  │
          │  .tfstate       │   │  Docker image    │   │  │  EC2 t3.micro │  │
          │  (state lock)   │   │                  │   │  │               │  │
          └─────────────────┘   └──────────────────┘   │  │ Docker        │  │
                                          │             │  │ container     │  │
                                          │  pull       │  │ Flask+Gunicorn│  │
                                          └────────────►│  │ port 80      │  │
                                                        │  └──────┬────────┘  │
                                                        │         │           │
                                                        │  ┌──────▼────────┐  │
                                                        │  │  RDS          │  │
                                                        │  │  PostgreSQL16 │  │
                                                        │  │  db.t3.micro  │  │
                                                        │  └───────────────┘  │
                                                        └─────────────────────┘
```

### Local Development

```
localhost:5000  →  app container  (Flask + Gunicorn)
                        │
                        │  DB_HOST=db (Docker internal DNS)
                        ▼
localhost:5432  →  db container   (PostgreSQL 16)

localhost:9090  →  prometheus     (scrapes /metrics every 15s)
localhost:3000  →  grafana        (dashboards over Prometheus)
```

---

## AWS Services

| Service | Purpose | Free Tier |
|---|---|---|
| EC2 (t3.micro) | Runs Docker container (Flask + Gunicorn) | 750 hrs/month |
| RDS PostgreSQL (db.t3.micro) | Persistent blog post storage | 750 hrs/month |
| ECR | Private Docker image registry | 500MB/month |
| S3 | Terraform remote state storage | 5GB |
| IAM | EC2 role to pull from ECR | Free |
| Security Groups | Firewall rules for EC2 and RDS | Free |

---

## Project Structure

```
aws-playground/
├── app/
│   ├── app.py              # Flask application (CRUD blog + /metrics endpoint)
│   ├── Dockerfile          # python:3.11-slim, gunicorn on port 80
│   └── requirements.txt    # flask, gunicorn, psycopg2-binary, prometheus-flask-exporter
│
├── scripts/
│   └── setup.sh.tpl        # EC2 boot script — pulls Docker image from ECR and runs it
│
├── bootstrap/              # One-time setup (NOT in git)
│   └── main.tf             # Creates S3 bucket + ECR repository
│
├── .github/
│   └── workflows/
│       └── terraform.yml   # CI/CD: build+push Docker image, then terraform apply
│
├── prometheus.yml          # Prometheus scrape config (scrapes app:80/metrics)
├── docker-compose.yml      # Local dev: app + db + prometheus + grafana
├── main.tf                 # Main infrastructure definition
├── .gitignore
└── README.md
```

---

## Infrastructure (main.tf)

```
main.tf defines:

  VPC (default)
  ├── IAM Role: blog-ec2-role  → AmazonEC2ContainerRegistryReadOnly
  ├── IAM Instance Profile: blog-ec2-profile
  │
  ├── Security Group: web-sg   → allows port 80 inbound
  ├── Security Group: rds-sg   → allows port 5432 from web-sg only
  │
  ├── EC2 Instance (t3.micro)
  │   ├── AMI: Amazon Linux 2023 (latest)
  │   ├── IAM profile: blog-ec2-profile (ECR pull access)
  │   ├── user_data: setup.sh.tpl (pulls Docker image, runs as systemd service)
  │   └── Security Group: web-sg
  │
  └── RDS Instance (db.t3.micro)
      ├── Engine: PostgreSQL 16
      ├── Storage: 20GB
      ├── DB: blogdb / bloguser
      ├── Security Group: rds-sg
      └── Not publicly accessible
```

---

## CI/CD Pipeline

```
On Pull Request:
  checkout → terraform init → fmt check → validate → plan → post plan as PR comment

On Merge to main:
  checkout → docker build → docker push to ECR → terraform init → terraform apply
```

### Secrets required in GitHub

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `DB_PASSWORD` | RDS PostgreSQL password |

---

## Docker

The app runs as a Docker container both locally and on AWS.

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 80
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:80", "app:app"]
```

### Local development

```bash
# start all services (app, postgres, prometheus, grafana)
docker compose up --build

# useful commands
docker ps                          # see running containers
docker logs -f aws_playground-app-1  # follow app logs
docker top aws_playground-app-1    # see processes inside container
docker stats                       # live CPU/memory per container

# connect to postgres directly
docker exec -it aws_playground-db-1 psql -U bloguser -d blogdb
```

---

## Observability (Local)

Prometheus + Grafana run locally via Docker Compose.

| Service | URL | Purpose |
|---|---|---|
| Flask app | `localhost:5000` | Blog |
| Metrics | `localhost:5000/metrics` | Raw Prometheus metrics |
| Prometheus | `localhost:9090` | Query metrics |
| Grafana | `localhost:3000` | Dashboards (admin/admin) |

### Grafana setup

1. Open `localhost:3000` → login: `admin` / `admin`
2. **Connections** → **Data sources** → **Add** → **Prometheus**
3. URL: `http://prometheus:9090` → **Save & test**
4. **≡** → **Explore** → select Prometheus → run queries

### Useful PromQL queries

```promql
# requests per second by route
rate(flask_http_request_total[1m])

# average response time
rate(flask_http_request_duration_seconds_sum[1m])
/ rate(flask_http_request_duration_seconds_count[1m])

# error rate
rate(flask_http_request_total{status="500"}[1m])
```

---

## Remote State

Terraform state is stored remotely in S3 so GitHub Actions and local machines share the same state.

```
S3 bucket:  utkarsh-tfstate-aws-playground
Key:        aws-playground/terraform.tfstate
Region:     ap-south-1
Locking:    S3 native locking (use_lockfile = true)
```

The bootstrap infrastructure is created once via `bootstrap/main.tf` and is never committed to git.

---

## Deploy

```bash
# First time — create S3 bucket + ECR (once only)
cd bootstrap && terraform init && terraform apply

# Build and push Docker image manually
docker build -t <ecr-url>:latest ./app
docker push <ecr-url>:latest

# Deploy infrastructure
terraform init
terraform apply -var="db_password=yourpassword"

# Destroy everything
terraform destroy -var="db_password=yourpassword"

# Via CI/CD — just push to main
git push origin main
```

---

## Cost (ap-south-1)

| Service | Free Tier | Outside Free Tier |
|---|---|---|
| EC2 t3.micro | $0.00 | ~$7.50/month |
| RDS db.t3.micro | $0.00 | ~$14.54/month |
| ECR | $0.00 (500MB) | ~$0.10/GB |
| S3 | $0.00 | ~$0.00 |
| **Total** | **$0.00** | **~$22/month** |

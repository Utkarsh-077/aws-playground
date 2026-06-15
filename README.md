# Super Blog Bros

A full-stack blogging application deployed on AWS, styled after 8-bit Super Mario. Built as a hands-on DevOps playground covering Infrastructure as Code, CI/CD pipelines, and AWS cloud services.

---

## Architecture

```
                        ┌─────────────────────────────────────────┐
                        │              GitHub                      │
                        │                                          │
                        │  ┌──────────┐      ┌─────────────────┐  │
                        │  │  app/    │      │ .github/        │  │
                        │  │  app.py  │      │ workflows/      │  │
                        │  │  req.txt │      │ terraform.yml   │  │
                        │  └──────────┘      └────────┬────────┘  │
                        └───────────────────────────┬─┴───────────┘
                                                    │
                                          git push to main
                                                    │
                                                    ▼
                        ┌─────────────────────────────────────────┐
                        │          GitHub Actions Runner           │
                        │                                          │
                        │  1. terraform init   (reads S3 state)   │
                        │  2. terraform plan   (preview changes)  │
                        │  3. terraform apply  (deploy to AWS)    │
                        └─────────────────┬───────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                      │
                    ▼                     ▼                      ▼
          ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
          │   S3 Bucket     │   │    DynamoDB     │   │   AWS (Mumbai)  │
          │                 │   │                 │   │                 │
          │  terraform      │   │  State locking  │   │  ┌───────────┐  │
          │  .tfstate       │   │  (tfstate-lock) │   │  │  EC2      │  │
          │                 │   │                 │   │  │ t3.micro  │  │
          └─────────────────┘   └─────────────────┘   │  │           │  │
                                                       │  │ Flask +   │  │
                                                       │  │ Gunicorn  │  │
                                                       │  │ port 80   │  │
                                                       │  └─────┬─────┘  │
                                                       │        │        │
                                                       │  ┌─────▼─────┐  │
                                                       │  │    RDS    │  │
                                                       │  │ PostgreSQL│  │
                                                       │  │ db.t3.    │  │
                                                       │  │ micro     │  │
                                                       │  └───────────┘  │
                                                       └─────────────────┘
```

---

## AWS Services

| Service | Purpose | Free Tier |
|---|---|---|
| EC2 (t3.micro) | Runs Flask + Gunicorn web server | 750 hrs/month |
| RDS PostgreSQL (db.t3.micro) | Persistent blog post storage | 750 hrs/month |
| S3 | Stores Terraform remote state | 5GB |
| DynamoDB | Terraform state locking | 25GB |
| Security Groups | Firewall rules for EC2 and RDS | Free |

---

## Project Structure

```
aws-playground/
├── app/
│   ├── app.py              # Flask application (CRUD blog)
│   └── requirements.txt    # Python dependencies
│
├── scripts/
│   └── setup.sh.tpl        # EC2 boot script (Terraform template)
│                           # Clones repo, installs deps, starts gunicorn
│
├── bootstrap/              # One-time setup (NOT in git)
│   └── main.tf             # Creates S3 bucket + DynamoDB for remote state
│
├── .github/
│   └── workflows/
│       └── terraform.yml   # CI/CD pipeline
│
├── main.tf                 # Main infrastructure definition
├── .gitignore
└── README.md
```

---

## Infrastructure (main.tf)

```
main.tf defines:

  VPC (default)
  ├── Security Group: web-sg   → allows port 80 inbound
  ├── Security Group: rds-sg   → allows port 5432 from web-sg only
  │
  ├── EC2 Instance (t3.micro)
  │   ├── AMI: Amazon Linux 2023 (latest)
  │   ├── user_data: setup.sh.tpl (clones GitHub repo, starts gunicorn)
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
  checkout → terraform init → terraform apply (auto-approve)
```

### Secrets required in GitHub

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `DB_PASSWORD` | RDS PostgreSQL password |

---

## Remote State

Terraform state is stored remotely in S3 so GitHub Actions and local machines share the same state.

```
S3 bucket:  utkarsh-tfstate-aws-playground
Key:        aws-playground/terraform.tfstate
Region:     ap-south-1
Locking:    S3 native locking
```

The bootstrap infrastructure (S3 bucket) is created once via `bootstrap/main.tf` and is never committed to git.

---

## Application

- **Framework:** Flask + Gunicorn (2 workers)
- **Database:** PostgreSQL via psycopg2
- **UI:** 8-bit Super Mario inspired (Press Start 2P font, pixel art CSS)
- **Features:** Create, Read, Update, Delete blog posts

### Running locally

```bash
cd app
pip3 install flask psycopg2-binary
DB_HOST=localhost DB_NAME=blogdb DB_USER=bloguser DB_PASSWORD=yourpassword \
  FLASK_APP=app.py flask run --port=5000
```

---

## Deploy

```bash
# First time setup
cd bootstrap && terraform init && terraform apply

# Deploy
terraform init
terraform apply -var="db_password=yourpassword"

# Destroy
terraform destroy -var="db_password=yourpassword"

# Via CI/CD — just push to main
git push origin main
```

---

## Cost (ap-south-1)

| | Free Tier | Outside Free Tier |
|---|---|---|
| EC2 t3.micro | $0.00 | ~$7.50/month |
| RDS db.t3.micro | $0.00 | ~$14.54/month |
| S3 + DynamoDB | $0.00 | ~$0.00 |
| **Total** | **$0.00** | **~$22/month** |

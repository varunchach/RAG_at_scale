# AWS Deployment Status — RAG at Scale

> **Purpose:** Hand-off notes for continuing the AWS deployment from any machine (Cursor, Claude Code, etc.)

---

## What This Repo Is

A production-style RAG (Retrieval-Augmented Generation) FastAPI service:

- **FastAPI + Uvicorn** on port 8000, Prometheus metrics on port 8001
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (FAISS + BM25 hybrid retrieval)
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **LLM:** AWS Bedrock — `us.anthropic.claude-haiku-4-5-20251001-v1:0` (cross-region inference profile)
- **UI:** Static HTML/JS served at `/` via FastAPI, talks to `/query` endpoint
- **Data:** 5 sample `.txt` docs loaded from `/app/data/raw/*.txt` at startup; 100+ corpus articles in `data/raw/corpus/`

---

## AWS Infrastructure (CloudFormation)

Template: `cloudformation/ecs-fargate-alb.yaml`

Resources created:
- ECS Fargate cluster + service (2 vCPU / 4 GB RAM, 1 task)
- Application Load Balancer (ALB) in default VPC
- IAM ExecutionRole + TaskRole (Bedrock + CloudWatch permissions)
- CloudWatch Log Group `/ecs/rag-at-scale-service`
- CloudWatch Observability Dashboard `rag-at-scale-observability`

---

## Current Deployment State

| Item | Status | Details |
|------|--------|---------|
| Docker image | ✅ Built & pushed | ECR: `593755927741.dkr.ecr.us-east-1.amazonaws.com/rag-at-scale-service:latest` |
| ECR login | ✅ Credentials cached | Docker Desktop has valid 12-hr token — no re-login needed yet |
| CloudFormation stack | ❌ NOT deployed | Command failed (see below) — stack `rag-at-scale` does not exist |
| ECS service | ❌ Not running | Depends on CF stack |
| ALB | ❌ Not created | Depends on CF stack |
| CloudWatch dashboard | ❌ Not created | Defined in CF template, deploys with stack |

---

## What Still Needs to Be Done

### Step 1 — Deploy CloudFormation Stack

The previous attempt failed due to a Windows path/quoting issue in the CLI invocation. Use PowerShell directly:

```powershell
$AWS = "C:\Users\Satej Raste\Downloads\Masai_Learning_Material\krishirakshak-project\venv\Scripts\aws.cmd"

& $AWS cloudformation deploy `
  --stack-name rag-at-scale `
  --template-file "C:\Users\Satej Raste\Downloads\Masai_Learning_Material\RAG_at_scale\cloudformation\ecs-fargate-alb.yaml" `
  --capabilities CAPABILITY_IAM `
  --region us-east-1 `
  --parameter-overrides `
    ProjectName=rag-at-scale `
    VpcId=vpc-0e0318f7665ce160e `
    PublicSubnetIds=subnet-0f0b03dad65cdb844,subnet-0ac60f15c5b2310ae,subnet-00bb4338053a9dece,subnet-0baef118b484d6f99,subnet-0372bd0af3868d46f,subnet-0504ddee11f65813d `
    ImageUri=593755927741.dkr.ecr.us-east-1.amazonaws.com/rag-at-scale-service:latest `
    ContainerPort=8000 `
    HealthCheckPath=/health `
    Cpu=2048 `
    Memory=4096 `
    DesiredCount=1
```

Expected time: ~3-5 minutes.

### Step 2 — Wait for ECS Service Stability

```powershell
$AWS = "C:\Users\Satej Raste\Downloads\Masai_Learning_Material\krishirakshak-project\venv\Scripts\aws.cmd"

$CLUSTER = (& $AWS cloudformation describe-stacks --stack-name rag-at-scale --region us-east-1 --query "Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue | [0]" --output text)
$SERVICE  = (& $AWS cloudformation describe-stacks --stack-name rag-at-scale --region us-east-1 --query "Stacks[0].Outputs[?OutputKey=='ServiceName'].OutputValue | [0]" --output text)

& $AWS ecs wait services-stable --cluster $CLUSTER --services $SERVICE --region us-east-1
```

### Step 3 — Smoke Test

```powershell
$AWS = "C:\Users\Satej Raste\Downloads\Masai_Learning_Material\krishirakshak-project\venv\Scripts\aws.cmd"
$ALB_URL = (& $AWS cloudformation describe-stacks --stack-name rag-at-scale --region us-east-1 --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerUrl'].OutputValue | [0]" --output text)
curl "$ALB_URL/health"
# Also open $ALB_URL in browser to see the UI
```

### Step 4 — Verify CloudWatch Dashboard

```powershell
$AWS = "C:\Users\Satej Raste\Downloads\Masai_Learning_Material\krishirakshak-project\venv\Scripts\aws.cmd"
$DASH = (& $AWS cloudformation describe-stacks --stack-name rag-at-scale --region us-east-1 --query "Stacks[0].Outputs[?OutputKey=='DashboardUrl'].OutputValue | [0]" --output text)
Write-Output "Dashboard: $DASH"
```

---

## AWS Configuration

| Item | Value |
|------|-------|
| AWS CLI path | `C:\Users\Satej Raste\Downloads\Masai_Learning_Material\krishirakshak-project\venv\Scripts\aws.cmd` |
| Region | `us-east-1` |
| Account ID | `593755927741` |
| Default VPC | `vpc-0e0318f7665ce160e` |
| Public subnets | `subnet-0f0b03dad65cdb844`, `subnet-0ac60f15c5b2310ae`, `subnet-00bb4338053a9dece`, `subnet-0baef118b484d6f99`, `subnet-0372bd0af3868d46f`, `subnet-0504ddee11f65813d` |
| ECR registry | `593755927741.dkr.ecr.us-east-1.amazonaws.com` |
| ECR repo | `rag-at-scale-service` |
| Bedrock model | `us.anthropic.claude-haiku-4-5-20251001-v1:0` (confirmed ACTIVE) |

### ECR Re-login (if needed — token expires after 12 hours)

**Use PowerShell** (not cmd.exe pipe — it mangles the token on Windows):
```powershell
$AWS = "C:\Users\Satej Raste\Downloads\Masai_Learning_Material\krishirakshak-project\venv\Scripts\aws.cmd"
$TOKEN = (& $AWS ecr get-login-password --region us-east-1)
$TOKEN | docker login --username AWS --password-stdin 593755927741.dkr.ecr.us-east-1.amazonaws.com
```

---

## Dockerfile Changes Made (Critical)

`docker/Dockerfile` was updated to pre-download HuggingFace models **as the `app` user** (not root) and disable runtime HF network calls:

```dockerfile
USER app

RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
print('Models pre-downloaded OK')"

ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1
```

Without this, models would download to `/root/.cache` during build but the runtime `app` user looks in `/home/app/.cache` — causing re-download on every cold start (60-90s delay) or failure if HuggingFace is unreachable.

---

## CloudFormation Changes Made

`cloudformation/ecs-fargate-alb.yaml` additions:
1. **ExecutionRole** — added `CloudWatchLogsExtended` inline policy (CreateLogGroup, CreateLogStream, PutLogEvents)
2. **TaskRole** — added `bedrock:ListFoundationModels` + new `CloudWatchMetrics` policy
3. **ObservabilityDashboard** — full CloudWatch dashboard with ECS CPU/Memory/Tasks + ALB RequestCount/Latency(p50/p95/p99)/4xx/5xx/HealthyHosts widgets + CloudWatch Logs Insights live stream

---

## If Starting Fresh (Image Already in ECR)

You do NOT need to rebuild or re-push the Docker image. Just run Steps 1-4 above.
If the ECR token has expired (>12 hours since last push), re-login first using the PowerShell command above.

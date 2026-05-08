# RAG at Scale Setup Guide

This guide covers local setup, notebook execution, the baseline AWS app, and the separate eval app.

## Prerequisites

- Python `3.11`
- Java `11` or `17` for Spark
- AWS CLI configured for `us-east-1`
- Docker Desktop only if you want to build the baseline image locally

## Local Environment

### Create and activate the virtual environment

macOS or Linux:

```bash
python3.11 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install ipykernel jupyterlab nbconvert
```

### Register the notebook kernel

```bash
python -m ipykernel install --user --name rag-at-scale --display-name "RAG at Scale (py3.11)"
```

## AWS Credentials

Configure AWS credentials in the same shell where you will run the notebook or deployment scripts:

```bash
aws configure
aws sts get-caller-identity
```

Optional Bedrock override:

```bash
export BEDROCK_MODEL_ID="your-inference-profile-id-or-arn"
```

## Run the Notebook

```bash
jupyter lab
```

Open `RAG_Demo_Docker.ipynb` and choose the `rag-at-scale` kernel.

For a non-interactive smoke run:

```bash
jupyter nbconvert --to notebook --execute RAG_Demo_Docker.ipynb --output RAG_Demo_Docker.executed.ipynb
```

## Run the App Locally

```bash
uvicorn src.service.app:app --host 0.0.0.0 --port 8000 --reload
```

Useful endpoints:

- `http://localhost:8000/`
- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8001/metrics`

## Baseline AWS App

Use the baseline deployment for the stable production-style demo app.

```bash
bash scripts/deploy_aws.sh
```

Status:

```bash
bash scripts/deploy_aws.sh status
```

This creates the `rag-at-scale` stack and a baseline dashboard.

## Separate Eval AWS App

Use the separate eval deployment when you want LLM-as-judge scoring without touching the baseline app.

```bash
bash scripts/deploy_eval_app.sh deploy
```

Status:

```bash
bash scripts/deploy_eval_app.sh status
```

This creates a second isolated stack:

- stack: `rag-at-scale-eval`
- service: `rag-at-scale-eval-service`
- ECR repo: `rag-at-scale-eval-service`
- dashboard: `rag-at-scale-eval-observability`

The eval deployment uses a remote native `amd64` build in AWS CodeBuild, then deploys the resulting image into its own ECS stack.

## Two-Stack Demo Model

The repo now supports:

1. `rag-at-scale`
   - stable baseline app
   - good fallback for demos

2. `rag-at-scale-eval`
   - separate eval app
   - async LLM-as-judge
   - separate CloudWatch metrics and dashboard

## Troubleshooting

- `ModuleNotFoundError: pyspark`
  - activate the repo virtual environment first
- `JAVA_HOME not set`
  - install JDK `11` or `17` and export `JAVA_HOME`
- Bedrock `AccessDeniedException`
  - enable Bedrock model access in AWS
- slow local image builds on Apple Silicon
  - use `scripts/deploy_eval_app.sh` for the eval app, because it builds remotely on native `amd64`

## Recommended Reading

- `README.md`
- `DEPLOYMENT_STATUS.md`
- `docs/APP_ASSEMBLY_GUIDE.md`
- `docs/NEXUS_SAMPLE_QA.md`

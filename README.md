# RAG at Scale

This repository contains a teaching-friendly RAG application that demonstrates:

- document ingestion from PDF
- dense + sparse hybrid retrieval
- reranking with a cross-encoder
- answer generation with AWS Bedrock
- operational observability with logs, traces, metrics, and dashboards
- an isolated LLM-as-judge deployment for evaluation demos

## What Is In The Repo

- `RAG_Demo_Docker.ipynb`: the main notebook demo
- `src/`: FastAPI service, retrieval, embeddings, and observability code
- `data/raw/`: startup sample corpus plus the Nexus PDF used for demos
- `cloudformation/ecs-fargate-alb.yaml`: ECS Fargate + ALB + CloudWatch infrastructure
- `scripts/deploy_aws.sh`: baseline app deployment
- `scripts/deploy_eval_app.sh`: separate eval app deployment via remote amd64 build
- `docs/APP_ASSEMBLY_GUIDE.md`: end-to-end assembly and deployment guide
- `docs/NEXUS_SAMPLE_QA.md`: Nexus sample questions and expected answers
- `DEPLOYMENT_STATUS.md`: current handoff and deployment notes

## Quick Start

### Local Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install ipykernel jupyterlab nbconvert
```

### Run The App Locally

```bash
uvicorn src.service.app:app --host 0.0.0.0 --port 8000 --reload
```

Useful local URLs:

- `http://localhost:8000/`
- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8001/metrics`

### Run The Notebook

```bash
jupyter lab
```

Open `RAG_Demo_Docker.ipynb` and select the `rag-at-scale` kernel.

## AWS Deployment Modes

There are now two deployment shapes.

### 1. Baseline App

The baseline app is the stable production-style RAG service without eval scoring turned on.

```bash
bash scripts/deploy_aws.sh
```

This creates resources under the `rag-at-scale` name set.

### 2. Separate Eval App

The eval app is deployed as a separate stack, image, service, ALB, and dashboard so the baseline app stays untouched.

```bash
bash scripts/deploy_eval_app.sh deploy
```

This creates resources under the `rag-at-scale-eval` name set and enables:

- LLM-as-judge scoring
- CloudWatch custom metrics for evals
- eval-specific dashboard widgets

## Two-Stack Model

The repo intentionally supports two parallel AWS apps:

- `rag-at-scale`
  - baseline app
  - safe fallback during demos
- `rag-at-scale-eval`
  - eval-enabled app
  - judge scores and eval dashboard

This keeps the demo stable while still allowing experiments.

## Recommended Demo Flow

1. Show the baseline app first.
2. Show the eval app second.
3. Ingest `data/raw/nexus_research_bulletin_2025.pdf` into the eval app.
4. Ask a fact-rich Nexus question.
5. Show the answer, then open the eval dashboard and log stream.

## Documentation

- setup guide: `SETUP.md`
- assembly guide: `docs/APP_ASSEMBLY_GUIDE.md`
- Nexus Q&A guide: `docs/NEXUS_SAMPLE_QA.md`
- deployment handoff: `DEPLOYMENT_STATUS.md`

## Testing

Run the focused test suite with:

```bash
pytest tests/test_service.py tests/test_evals.py
```

Or run the full suite:

```bash
pytest tests/
```

## Repo Layout

```text
RAG_at_scale/
├── RAG_Demo_Docker.ipynb
├── README.md
├── SETUP.md
├── DEPLOYMENT_STATUS.md
├── docs/
├── cloudformation/
├── data/
├── docker/
├── scripts/
├── src/
└── tests/
```

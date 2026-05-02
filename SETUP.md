# RAG at Scale — Setup & Installation Guide

Run the full demo locally on **Windows, macOS, or Linux** using a Python 3.11 virtual environment.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | **3.11.x** | PySpark 3.5 does not work with Python 3.12+ |
| Java JDK | 11 or 17 | Required by Apache Spark |
| AWS CLI | any | For the Bedrock (Claude) section |
| Docker Desktop | any | Optional — for the Docker deploy section |

### Install Python 3.11

- **Windows**: download from https://www.python.org/downloads/release/python-3118/ and check "Add to PATH"
- **macOS**: `brew install python@3.11`
- **Linux**: `sudo apt install python3.11 python3.11-venv` (Ubuntu/Debian)

### Install Java

- **Windows / macOS / Linux**: https://adoptium.net/temurin/releases/?version=17
- **macOS (Homebrew alternative)**:
  ```bash
  brew install openjdk@17
  export JAVA_HOME="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
  export PATH="$JAVA_HOME/bin:$PATH"
  ```
- Verify: `java -version`

---

## Windows-only: Hadoop `winutils.exe`

PySpark on Windows requires Hadoop native binaries for filesystem operations.

```powershell
# 1. Create folder
New-Item -ItemType Directory -Force -Path C:\hadoop\bin

# 2. Download winutils.exe for Hadoop 3.x
# Get it from: https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.5/bin
# Place winutils.exe and hadoop.dll in C:\hadoop\bin\

# 3. Set environment variable (the notebook sets it automatically, but you can also persist it)
[System.Environment]::SetEnvironmentVariable('HADOOP_HOME', 'C:\hadoop', 'User')
```

> The notebook sets `HADOOP_HOME` automatically from cell 0 — you only need the files to be present.

---

## Setup Steps

### 1. Clone the repository

```bash
git clone https://github.com/varunchach/RAG_at_scale.git
cd RAG_at_scale
```

### 2. Create a Python 3.11 virtual environment

**Windows (PowerShell):**
```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install ipykernel jupyterlab nbconvert
```

> Installation takes 3-10 minutes and may download large ML models on first run.

### 4. Register the Jupyter kernel

```bash
python -m ipykernel install --user --name rag-at-scale --display-name "RAG at Scale (py3.11)"
```

### 5. Configure AWS credentials (for Section 7B — Bedrock)

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1`
- Output format: `json`

Verify access:
```bash
aws sts get-caller-identity
```

Optional for newer Bedrock models that require an inference profile:
```bash
export BEDROCK_MODEL_ID="your-inference-profile-id-or-arn"
```

---

## Running the Notebook

### In VS Code (recommended)

1. Open the project folder in VS Code
2. Install the **Jupyter** extension
3. Open `RAG_Demo_Docker.ipynb`
4. Click the kernel selector (top-right) → choose **"RAG at Scale (py3.11)"**
5. Run **Cell → Run All** (or Shift+Enter cell by cell)

### In Jupyter Lab

```bash
# With venv activated:
pip install jupyterlab
jupyter lab
```

Open `RAG_Demo_Docker.ipynb`, select kernel **"RAG at Scale (py3.11)"**, then run.

### Execute non-interactively (useful for smoke tests)

```bash
jupyter nbconvert --to notebook --execute RAG_Demo_Docker.ipynb --output RAG_Demo_Docker.executed.ipynb
```

> If AWS credentials are not configured yet, the Bedrock setup cell will warn you, but the rest of the notebook should still run.

---

## Running the Application

```bash
uvicorn src.service.app:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8001/metrics`

### In Cursor

1. Open project folder in Cursor
2. Open `RAG_Demo_Docker.ipynb`
3. Select kernel **"RAG at Scale (py3.11)"** from the kernel picker
4. Run cells

---

## Project Structure

```
RAG_at_scale/
├── RAG_Demo_Docker.ipynb   # Main demo notebook (start here)
├── requirements.txt         # Local Python dependencies (includes AWS CLI + tests)
├── data/
│   └── raw/                 # 5 sample .txt documents (RAG/ML themed)
├── src/
│   ├── embeddings/          # SparkEmbedder (sentence-transformers)
│   ├── retrieval/           # HybridSearch (FAISS + BM25) + Reranker
│   ├── service/             # FastAPI app (handlers, models, app.py)
│   └── observability/       # Structured logging, OpenTelemetry, Prometheus
├── tests/                   # pytest test suite
├── docker/                  # Dockerfile for production image
├── kubernetes/              # HPA manifest for K8s autoscaling
└── scripts/                 # deploy_aws.sh (ECR + ECS rolling deploy)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: pyspark` | Activate venv: `.\venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` |
| `JAVA_HOME not set` | Install JDK 11/17 and add to PATH; restart terminal |
| `winutils.exe not found` | Place `winutils.exe` + `hadoop.dll` in `C:\hadoop\bin\` |
| `PyArrow must be installed` | `pip install pyarrow` (already in requirements.txt) |
| Kernel not appearing in VS Code | Re-run `python -m ipykernel install --user --name rag-at-scale` |
| AWS `UnrecognizedClientException` | Run `aws configure` and enter valid credentials |
| Bedrock `AccessDeniedException` | Enable model access in AWS Console → Bedrock → Model Access |
| `ModuleNotFoundError: service` or `retrieval` | Run the app with `uvicorn src.service.app:app` from the repo root |

---

## Docker (Alternative — no local Python setup needed)

```bash
# Start the full stack
docker-compose -f docker-compose-demo.yml up

# Notebook is available at:
# http://localhost:8888?token=ragdemo
```

The Docker image includes Python, PySpark, and all dependencies pre-installed.

---

## One-Click AWS Deployment

The repository now includes a one-command AWS deployment path for the FastAPI service using:

- CloudFormation
- Amazon ECR
- Amazon ECS Fargate
- Application Load Balancer
- CloudWatch Logs

### Prerequisites

- Docker Desktop running locally
- AWS CLI configured with permissions for CloudFormation, ECS, ECR, IAM, EC2, ELBv2, and CloudWatch Logs
- A default VPC with at least 2 public subnets in your target AWS region

### Deploy

```bash
bash scripts/deploy_aws.sh
```

### Check Status

```bash
bash scripts/deploy_aws.sh status
```

### Expected Time

The first deployment usually takes **8-15 minutes**:

1. discover the default VPC and public subnets
2. create/update the ECR repository
3. build Docker image
4. push image to ECR
5. create/update the ECS Fargate + ALB stack
6. wait for ALB health checks to pass

This is intentionally the minimal from-scratch path:

- one shell command
- one CloudFormation stack
- one ECS Fargate service
- one public ALB
- one CloudWatch log group
- default VPC networking

### AWS Console Walkthrough for Students

After deployment, use these pages for a live demo:

1. **CloudFormation** → stack events and outputs
2. **ECR** → pushed image
3. **ECS** → service, tasks, health checks
4. **ALB DNS name** → live app endpoint
5. **CloudWatch Logs** → live request logs

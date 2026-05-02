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
```

> Installation takes 3-10 minutes (downloads PyTorch + sentence-transformers models).

### 4. Register the Jupyter kernel

```bash
pip install ipykernel
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
├── requirements.txt         # All Python dependencies
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

---

## Docker (Alternative — no local Python setup needed)

```bash
# Start the full stack
docker-compose -f docker-compose-demo.yml up

# Notebook is available at:
# http://localhost:8888?token=ragdemo
```

The Docker image includes Python, PySpark, and all dependencies pre-installed.

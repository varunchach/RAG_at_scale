# 🚀 RAG at Scale: Complete Student Demo

**Topics Covered:**
1. **RAG at Scale w/ Spark**: Spark embed gen, hybrid search, rerank, Docker, cloud deploy
2. **Distributed Embeddings**: PySpark UDFs, GPU scheduling, cluster tuning
3. **Service Observability**: Logs, traces, metrics, autoscale

## Quick Start

### 1. Setup Environment
```bash
# Activate your existing venv
& 'C:\Users\Satej Raste\Downloads\Masai_Learning_Material\krishirakshak-project\venv\Scripts\Activate.ps1'

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Complete Demo
```bash
# Start the notebook
jupyter notebook RAG_at_Scale_Complete.ipynb
```

### 3. Run Individual Components
```bash
# Start the service
python -m src.service.app

# Start with Docker
docker-compose -f docker/docker-compose.yml up --build
```

## Project Structure

```
RAG_at_scale/
├── RAG_at_Scale_Complete.ipynb    # Main demo notebook
├── data/                          # Sample data and embeddings
├── src/                           # Source code
│   ├── embeddings/                # PySpark embedding generation
│   ├── retrieval/                 # Hybrid search & reranking
│   ├── observability/             # Logging, tracing, metrics
│   └── service/                   # FastAPI service
├── docker/                        # Containerization
├── kubernetes/                    # Cloud deployment
├── tests/                         # Unit tests
└── scripts/                       # Deployment scripts
```

## Learning Outcomes

By the end of this demo, you'll understand:

✅ **Distributed ML Pipelines**: Build with PySpark  
✅ **GPU-Accelerated UDFs**: For embedding generation  
✅ **Hybrid Search Systems**: Dense + sparse retrieval  
✅ **Reranking**: Cross-encoder relevance scoring  
✅ **Observability**: Logs, traces, metrics at scale  
✅ **Containerization**: Docker for ML services  
✅ **Cloud Deployment**: AWS ECS with auto-scaling  

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `POST /search` - RAG search
- `POST /embeddings` - Generate embeddings

## Monitoring

- **API**: http://localhost:8000
- **Metrics**: http://localhost:8001/metrics
- **Grafana**: http://localhost:3000 (admin/admin)

## Deployment

### Local Development
```bash
# Run everything locally
docker-compose -f docker/docker-compose.yml up --build
```

### AWS Deployment
```bash
# Deploy to AWS ECS
bash scripts/deploy_aws.sh
```

## Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Sample Data

Generate sample documents for testing:
```bash
python scripts/generate_sample_data.py
```

## Testing

Run the test suite:
```bash
pytest tests/
```

---

**Happy Learning! 🎓**

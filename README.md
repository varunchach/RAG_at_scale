# 🚀 RAG at Scale: Complete Student Demo

**Topics Covered:**
1. **RAG at Scale w/ Spark**: Spark embed gen, hybrid search, rerank, Docker, cloud deploy
2. **Distributed Embeddings**: PySpark UDFs, GPU scheduling, cluster tuning
3. **Service Observability**: Logs, traces, metrics, autoscale

## Quick Start

### 1. Setup Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install ipykernel jupyterlab nbconvert
```

### 2. Run the Complete Demo
```bash
# Start the notebook
jupyter notebook RAG_Demo_Docker.ipynb
```

### 3. Run Individual Components
```bash
# Start the service
uvicorn src.service.app:app --host 0.0.0.0 --port 8000 --reload

# Start with Docker
docker-compose -f docker/docker-compose.yml up --build
```

## Project Structure

```
RAG_at_scale/
├── RAG_Demo_Docker.ipynb          # Main demo notebook
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
# One-click deploy to AWS (minimal path)
bash scripts/deploy_aws.sh

# Check deployment status later
bash scripts/deploy_aws.sh status
```

This minimal flow uses:

- an ECR repository
- a single CloudFormation stack
- the region's default VPC + public subnets
- one ECS Fargate cluster + service
- one internet-facing ALB
- one CloudWatch log group + ECS IAM roles

First deploy usually takes **8-15 minutes** because it includes Docker build, ECR push, stack creation, and the initial ECS task startup.

If your AWS account does not have a default VPC, the script stops and tells you to create or restore one first.

### Live AWS Demo

Once deployed, show students these AWS console views in order:

1. **CloudFormation**: watch stack creation and outputs
2. **ECR**: show the pushed application image
3. **ECS**: show task rollout and service health
4. **EC2 / Load Balancers**: open the ALB DNS name
5. **CloudWatch Logs**: show live request logs

The deploy script prints the public app URL when the service becomes healthy.

## Configuration

Optional: create `.env` if you want to override defaults such as `OTLP_ENDPOINT`.

```bash
cat > .env <<'EOF'
OTLP_ENDPOINT=
EOF
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

#!/bin/bash
# AWS Deployment Script — ECR push + ECS rolling deploy

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
REPO_NAME="rag-service"
CLUSTER_NAME="rag-cluster"
SERVICE_NAME="rag-service"

echo "🚀 Starting AWS deployment (region: $REGION)..."

# ── 1. Build Docker image ──────────────────────────────────────────────────
echo "📦 Building Docker image..."
docker build -f docker/Dockerfile -t "$REPO_NAME:latest" .

# ── 2. Get AWS account ID ─────────────────────────────────────────────────
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME"

# ── 3. Ensure ECR repository exists ──────────────────────────────────────
echo "🗄️  Checking ECR repository..."
if ! aws ecr describe-repositories --repository-names "$REPO_NAME" \
        --region "$REGION" > /dev/null 2>&1; then
    echo "   Creating ECR repository: $REPO_NAME"
    aws ecr create-repository \
        --repository-name "$REPO_NAME" \
        --region "$REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    echo "   ✅ Repository created"
else
    echo "   ✅ Repository already exists"
fi

# ── 4. Authenticate Docker with ECR ──────────────────────────────────────
echo "🔑 Logging in to ECR..."
aws ecr get-login-password --region "$REGION" \
    | docker login --username AWS --password-stdin \
      "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# ── 5. Tag and push image ─────────────────────────────────────────────────
echo "⬆️  Pushing image to ECR..."
docker tag "$REPO_NAME:latest" "$ECR_URI:latest"
docker push "$ECR_URI:latest"
echo "   ✅ Image pushed: $ECR_URI:latest"

# ── 6. Force ECS rolling deploy ───────────────────────────────────────────
echo "🚢 Triggering ECS rolling deployment..."
aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --force-new-deployment \
    --region "$REGION"

echo ""
echo "✅ Deployment triggered!"
echo "   Monitor progress:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION"
echo ""
echo "   CloudWatch logs:"
echo "   aws logs tail /aws/ecs/$SERVICE_NAME --follow --region $REGION"

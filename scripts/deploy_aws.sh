#!/bin/bash
# Minimal one-click AWS deployment for the RAG at Scale FastAPI service.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ACTION="${1:-deploy}"
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-rag-at-scale}"
STACK_NAME="${STACK_NAME:-${PROJECT_NAME}}"
REPO_NAME="${REPO_NAME:-${PROJECT_NAME}-service}"
CONTAINER_PORT="${CONTAINER_PORT:-8000}"
HEALTH_CHECK_PATH="${HEALTH_CHECK_PATH:-/health}"
ECS_TASK_CPU="${ECS_TASK_CPU:-2048}"
ECS_TASK_MEMORY="${ECS_TASK_MEMORY:-4096}"
ECS_DESIRED_COUNT="${ECS_DESIRED_COUNT:-1}"

if git -C "$REPO_ROOT" rev-parse --short HEAD >/dev/null 2>&1; then
    DEFAULT_IMAGE_TAG="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
else
    DEFAULT_IMAGE_TAG="$(date +%Y%m%d%H%M%S)"
fi
IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}"

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "❌ Missing required command: $1"
        exit 1
    fi
}

ensure_prerequisites() {
    require_cmd aws
    require_cmd docker
    require_cmd curl
    aws sts get-caller-identity --region "$REGION" >/dev/null
    docker ps >/dev/null
}

stack_exists() {
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" >/dev/null 2>&1
}

stack_output() {
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" \
        --output text
}

discover_default_network() {
    DEFAULT_VPC_ID="$(aws ec2 describe-vpcs \
        --filters Name=isDefault,Values=true \
        --region "$REGION" \
        --query 'Vpcs[0].VpcId' \
        --output text)"

    if [[ -z "$DEFAULT_VPC_ID" || "$DEFAULT_VPC_ID" == "None" ]]; then
        echo "❌ No default VPC found in $REGION."
        echo "   For the minimal path, create or restore a default VPC first."
        exit 1
    fi

    DEFAULT_SUBNETS_RAW="$(aws ec2 describe-subnets \
        --filters Name=vpc-id,Values="$DEFAULT_VPC_ID" Name=map-public-ip-on-launch,Values=true \
        --region "$REGION" \
        --query 'Subnets[].SubnetId' \
        --output text)"

    if [[ -z "$DEFAULT_SUBNETS_RAW" || "$DEFAULT_SUBNETS_RAW" == "None" ]]; then
        echo "❌ No public subnets found in default VPC $DEFAULT_VPC_ID."
        exit 1
    fi

    DEFAULT_SUBNETS="$(tr '\t' ',' <<<"$DEFAULT_SUBNETS_RAW")"
    SUBNET_COUNT="$(tr ',' '\n' <<<"$DEFAULT_SUBNETS" | sed '/^$/d' | wc -l | tr -d ' ')"

    if [[ "$SUBNET_COUNT" -lt 2 ]]; then
        echo "❌ Need at least 2 public subnets for an ALB. Found $SUBNET_COUNT."
        exit 1
    fi
}

ensure_ecr_repository() {
    ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text --region "$REGION")"
    ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
    ECR_URI="${ECR_REGISTRY}/${REPO_NAME}"

    if ! aws ecr describe-repositories \
        --repository-names "$REPO_NAME" \
        --region "$REGION" >/dev/null 2>&1; then
        echo "🗄️  Creating ECR repository: $REPO_NAME"
        aws ecr create-repository \
            --repository-name "$REPO_NAME" \
            --region "$REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256 >/dev/null
    else
        echo "🗄️  Reusing ECR repository: $REPO_NAME"
    fi
}

build_and_push_image() {
    local local_image
    local image_uri

    local_image="${REPO_NAME}:${IMAGE_TAG}"
    image_uri="${ECR_URI}:${IMAGE_TAG}"

    echo "🔑 Logging in to ECR..."
    aws ecr get-login-password --region "$REGION" \
        | docker login --username AWS --password-stdin "$ECR_REGISTRY"

    echo "📦 Building Docker image: $local_image"
    docker build -f "$REPO_ROOT/docker/Dockerfile" \
        -t "$local_image" \
        -t "$image_uri" \
        -t "${ECR_URI}:latest" \
        "$REPO_ROOT"

    echo "⬆️  Pushing image to ECR..."
    docker push "$image_uri"
    docker push "${ECR_URI}:latest"

    IMAGE_URI="$image_uri"
}

deploy_stack() {
    echo "🏗️  Deploying minimal Fargate stack: $STACK_NAME"
    aws cloudformation deploy \
        --stack-name "$STACK_NAME" \
        --template-file "$REPO_ROOT/cloudformation/ecs-fargate-alb.yaml" \
        --capabilities CAPABILITY_IAM \
        --region "$REGION" \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            VpcId="$DEFAULT_VPC_ID" \
            PublicSubnetIds="$DEFAULT_SUBNETS" \
            ImageUri="$IMAGE_URI" \
            ContainerPort="$CONTAINER_PORT" \
            HealthCheckPath="$HEALTH_CHECK_PATH" \
            Cpu="$ECS_TASK_CPU" \
            Memory="$ECS_TASK_MEMORY" \
            DesiredCount="$ECS_DESIRED_COUNT"
}

wait_for_service() {
    local cluster_name
    local service_name

    cluster_name="$(stack_output ClusterName)"
    service_name="$(stack_output ServiceName)"

    echo "⏳ Waiting for ECS service stability..."
    aws ecs wait services-stable \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$REGION"
}

smoke_test_url() {
    local app_url
    local attempt

    app_url="$(stack_output LoadBalancerUrl)"
    echo "🩺 Running smoke test against ${app_url}${HEALTH_CHECK_PATH}"

    for attempt in {1..12}; do
        if curl -fsS "${app_url}${HEALTH_CHECK_PATH}" >/dev/null 2>&1; then
            echo "✅ Smoke test passed"
            return
        fi
        sleep 10
    done

    echo "⚠️  Smoke test did not pass yet. The service may still be warming up."
}

print_summary() {
    local cluster_name
    local service_name
    local app_url
    local log_group_name

    cluster_name="$(stack_output ClusterName)"
    service_name="$(stack_output ServiceName)"
    app_url="$(stack_output LoadBalancerUrl)"
    log_group_name="$(stack_output LogGroupName)"

    echo
    echo "✅ Minimal AWS deployment complete"
    echo "   Region:        $REGION"
    echo "   Default VPC:   $DEFAULT_VPC_ID"
    echo "   ECR repo:      $REPO_NAME"
    echo "   ECS cluster:   $cluster_name"
    echo "   ECS service:   $service_name"
    echo "   Image:         $IMAGE_URI"
    echo "   App URL:       $app_url"
    echo "   Health check:  ${app_url}${HEALTH_CHECK_PATH}"
    echo
    echo "AWS console walkthrough:"
    echo "  CloudFormation -> stack ${STACK_NAME}"
    echo "  ECR            -> repo ${REPO_NAME}"
    echo "  ECS            -> cluster ${cluster_name} -> service ${service_name}"
    echo "  CloudWatch     -> log group ${log_group_name}"
    echo
    echo "Helpful commands:"
    echo "  bash scripts/deploy_aws.sh status"
    echo "  aws logs tail ${log_group_name} --follow --region ${REGION}"
}

show_status() {
    local stack_status
    local cluster_name
    local service_name

    if ! stack_exists; then
        echo "ℹ️  Stack not found: $STACK_NAME"
        echo "   Run: bash scripts/deploy_aws.sh"
        return
    fi

    stack_status="$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text)"
    cluster_name="$(stack_output ClusterName)"
    service_name="$(stack_output ServiceName)"

    echo "Stack: $STACK_NAME ($stack_status)"
    echo "App URL: $(stack_output LoadBalancerUrl)"
    aws ecs describe-services \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$REGION" \
        --query 'services[0].{Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount,TaskDefinition:taskDefinition}' \
        --output table
}

show_help() {
    cat <<EOF
Usage: bash scripts/deploy_aws.sh [deploy|status|help]

Commands:
  deploy   Build the image, ensure ECR exists, and deploy one minimal ECS Fargate + ALB stack.
  status   Show CloudFormation and ECS service status for the deployed stack.
  help     Show this help text.

Defaults:
  - Uses the default VPC in the selected region
  - Uses public subnets with auto-assigned public IPs
  - Deploys a single ECS Fargate service behind one ALB

Environment overrides:
  AWS_REGION        AWS region (default: us-east-1)
  PROJECT_NAME      Resource prefix (default: rag-at-scale)
  STACK_NAME        CloudFormation stack name (default: rag-at-scale)
  REPO_NAME         ECR repository name (default: rag-at-scale-service)
  ECS_TASK_CPU      Fargate CPU units (default: 2048)
  ECS_TASK_MEMORY   Fargate memory in MiB (default: 4096)
  ECS_DESIRED_COUNT Desired ECS task count (default: 1)
  IMAGE_TAG         Docker image tag (default: git sha or timestamp)
EOF
}

deploy() {
    ensure_prerequisites
    discover_default_network
    ensure_ecr_repository
    build_and_push_image
    deploy_stack
    wait_for_service
    smoke_test_url
    print_summary
}

case "$ACTION" in
    deploy)
        deploy
        ;;
    status)
        ensure_prerequisites
        show_status
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $ACTION"
        show_help
        exit 1
        ;;
esac

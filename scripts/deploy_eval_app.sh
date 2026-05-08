#!/bin/bash
# Build and deploy the eval-enabled app as a separate ECS service/stack.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_AWS="$REPO_ROOT/venv/bin/aws"

if [[ -x "$VENV_AWS" ]]; then
    export PATH="$REPO_ROOT/venv/bin:$PATH"
fi

ACTION="${1:-deploy}"
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-rag-at-scale-eval}"
STACK_NAME="${STACK_NAME:-${PROJECT_NAME}}"
REPO_NAME="${REPO_NAME:-${PROJECT_NAME}-service}"
BUILD_PROJECT="${BUILD_PROJECT:-${PROJECT_NAME}-builder}"
CODEBUILD_ROLE_NAME="${CODEBUILD_ROLE_NAME:-${PROJECT_NAME}-codebuild-role}"
CONTAINER_PORT="${CONTAINER_PORT:-8000}"
HEALTH_CHECK_PATH="${HEALTH_CHECK_PATH:-/health}"
ECS_TASK_CPU="${ECS_TASK_CPU:-2048}"
ECS_TASK_MEMORY="${ECS_TASK_MEMORY:-4096}"
ECS_DESIRED_COUNT="${ECS_DESIRED_COUNT:-1}"
ENABLE_LLM_JUDGE_EVALS="${ENABLE_LLM_JUDGE_EVALS:-true}"
ENABLE_CLOUDWATCH_APP_METRICS="${ENABLE_CLOUDWATCH_APP_METRICS:-true}"
EVAL_SAMPLE_RATE="${EVAL_SAMPLE_RATE:-1.0}"
EVAL_JUDGE_MODEL_ID="${EVAL_JUDGE_MODEL_ID:-us.anthropic.claude-haiku-4-5-20251001-v1:0}"
CLOUDWATCH_METRIC_NAMESPACE="${CLOUDWATCH_METRIC_NAMESPACE:-RAGAtScaleEval/Application}"
SOURCE_KEY="${SOURCE_KEY:-source/latest.zip}"
BASE_IMAGE_URI="${BASE_IMAGE_URI:-593755927741.dkr.ecr.us-east-1.amazonaws.com/rag-at-scale-service:latest}"

if git -C "$REPO_ROOT" rev-parse --short HEAD >/dev/null 2>&1; then
    DEFAULT_IMAGE_TAG="eval-$(git -C "$REPO_ROOT" rev-parse --short HEAD)-$(date +%Y%m%d%H%M%S)"
else
    DEFAULT_IMAGE_TAG="eval-$(date +%Y%m%d%H%M%S)"
fi
IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}"

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1"
        exit 1
    fi
}

ensure_prerequisites() {
    require_cmd aws
    require_cmd python3
    require_cmd curl
    aws sts get-caller-identity --region "$REGION" >/dev/null
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
        echo "No default VPC found in $REGION."
        exit 1
    fi

    DEFAULT_SUBNETS_RAW="$(aws ec2 describe-subnets \
        --filters Name=vpc-id,Values="$DEFAULT_VPC_ID" Name=map-public-ip-on-launch,Values=true \
        --region "$REGION" \
        --query 'Subnets[].SubnetId' \
        --output text)"

    if [[ -z "$DEFAULT_SUBNETS_RAW" || "$DEFAULT_SUBNETS_RAW" == "None" ]]; then
        echo "No public subnets found in default VPC $DEFAULT_VPC_ID."
        exit 1
    fi

    DEFAULT_SUBNETS="$(tr '\t' ',' <<<"$DEFAULT_SUBNETS_RAW")"
}

ensure_ecr_repository() {
    ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text --region "$REGION")"
    ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
    EVAL_ECR_URI="${ECR_REGISTRY}/${REPO_NAME}"
    SOURCE_BUCKET="${SOURCE_BUCKET:-${PROJECT_NAME}-build-${ACCOUNT_ID}-${REGION}}"
    CODEBUILD_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${CODEBUILD_ROLE_NAME}"

    if ! aws ecr describe-repositories \
        --repository-names "$REPO_NAME" \
        --region "$REGION" >/dev/null 2>&1; then
        aws ecr create-repository \
            --repository-name "$REPO_NAME" \
            --region "$REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256 >/dev/null
    fi
}

ensure_source_bucket() {
    if aws s3api head-bucket --bucket "$SOURCE_BUCKET" >/dev/null 2>&1; then
        return
    fi

    if [[ "$REGION" == "us-east-1" ]]; then
        aws s3api create-bucket --bucket "$SOURCE_BUCKET" >/dev/null
    else
        aws s3api create-bucket \
            --bucket "$SOURCE_BUCKET" \
            --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
    fi
}

ensure_codebuild_role() {
    local trust_doc
    local policy_doc

    trust_doc="$(mktemp)"
    policy_doc="$(mktemp)"

    cat >"$trust_doc" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    cat >"$policy_doc" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::${SOURCE_BUCKET}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::${SOURCE_BUCKET}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:CompleteLayerUpload",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart"
      ],
      "Resource": [
        "arn:aws:ecr:${REGION}:${ACCOUNT_ID}:repository/rag-at-scale-service",
        "arn:aws:ecr:${REGION}:${ACCOUNT_ID}:repository/${REPO_NAME}"
      ]
    }
  ]
}
EOF

    if ! aws iam get-role --role-name "$CODEBUILD_ROLE_NAME" >/dev/null 2>&1; then
        aws iam create-role \
            --role-name "$CODEBUILD_ROLE_NAME" \
            --assume-role-policy-document "file://${trust_doc}" >/dev/null
        sleep 10
    fi

    aws iam put-role-policy \
        --role-name "$CODEBUILD_ROLE_NAME" \
        --policy-name "${BUILD_PROJECT}-inline" \
        --policy-document "file://${policy_doc}" >/dev/null

    rm -f "$trust_doc" "$policy_doc"
}

package_source_bundle() {
    SOURCE_ARCHIVE="$(mktemp "/tmp/${PROJECT_NAME}-source-XXXXXX.zip")"

    SOURCE_ARCHIVE="$SOURCE_ARCHIVE" REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

repo = Path(os.environ["REPO_ROOT"])
archive = Path(os.environ["SOURCE_ARCHIVE"])
include_files = [
    repo / "buildspec.eval.yml",
    repo / "requirements.eval.txt",
    repo / "docker" / "Dockerfile.eval",
]
include_dirs = [
    repo / "src",
]

with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zf:
    for path in include_files:
        zf.write(path, path.relative_to(repo))
    for root_dir in include_dirs:
        for path in root_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(repo))
PY
}

upload_source_bundle() {
    aws s3 cp "$SOURCE_ARCHIVE" "s3://${SOURCE_BUCKET}/${SOURCE_KEY}" >/dev/null
}

put_codebuild_project() {
    local project_doc

    project_doc="$(mktemp)"

    cat >"$project_doc" <<EOF
{
  "name": "${BUILD_PROJECT}",
  "description": "Builds the separate eval app image from the working production base image.",
  "source": {
    "type": "S3",
    "location": "${SOURCE_BUCKET}/${SOURCE_KEY}",
    "buildspec": "buildspec.eval.yml"
  },
  "artifacts": {
    "type": "NO_ARTIFACTS"
  },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/amazonlinux-x86_64-standard:5.0",
    "computeType": "BUILD_GENERAL1_MEDIUM",
    "privilegedMode": true,
    "environmentVariables": [
      {"name": "AWS_DEFAULT_REGION", "value": "${REGION}", "type": "PLAINTEXT"},
      {"name": "BASE_IMAGE_URI", "value": "${BASE_IMAGE_URI}", "type": "PLAINTEXT"},
      {"name": "EVAL_ECR_URI", "value": "${EVAL_ECR_URI}", "type": "PLAINTEXT"},
      {"name": "IMAGE_TAG", "value": "${IMAGE_TAG}", "type": "PLAINTEXT"}
    ]
  },
  "serviceRole": "${CODEBUILD_ROLE_ARN}",
  "timeoutInMinutes": 60,
  "queuedTimeoutInMinutes": 60
}
EOF

    if aws codebuild batch-get-projects --names "$BUILD_PROJECT" --region "$REGION" --query 'projects[0].name' --output text | grep -q "$BUILD_PROJECT"; then
        aws codebuild update-project --cli-input-json "file://${project_doc}" --region "$REGION" >/dev/null
    else
        aws codebuild create-project --cli-input-json "file://${project_doc}" --region "$REGION" >/dev/null
    fi

    rm -f "$project_doc"
}

run_remote_build() {
    local build_id
    local status
    local deep_link

    build_id="$(aws codebuild start-build \
        --project-name "$BUILD_PROJECT" \
        --region "$REGION" \
        --query 'build.id' \
        --output text)"

    echo "Started remote amd64 build: $build_id"

    while true; do
        status="$(aws codebuild batch-get-builds \
            --ids "$build_id" \
            --region "$REGION" \
            --query 'builds[0].buildStatus' \
            --output text)"

        case "$status" in
            SUCCEEDED)
                echo "Remote build succeeded"
                return
                ;;
            FAILED|FAULT|TIMED_OUT|STOPPED)
                deep_link="$(aws codebuild batch-get-builds \
                    --ids "$build_id" \
                    --region "$REGION" \
                    --query 'builds[0].logs.deepLink' \
                    --output text)"
                echo "Remote build failed with status: $status"
                echo "CodeBuild logs: $deep_link"
                exit 1
                ;;
            *)
                sleep 20
                ;;
        esac
    done
}

deploy_stack() {
    IMAGE_URI="${EVAL_ECR_URI}:${IMAGE_TAG}"
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
            DesiredCount="$ECS_DESIRED_COUNT" \
            EnableCloudWatchAppMetrics="$ENABLE_CLOUDWATCH_APP_METRICS" \
            EnableLlmJudgeEvals="$ENABLE_LLM_JUDGE_EVALS" \
            EvalSampleRate="$EVAL_SAMPLE_RATE" \
            EvalJudgeModelId="$EVAL_JUDGE_MODEL_ID" \
            CloudWatchMetricNamespace="$CLOUDWATCH_METRIC_NAMESPACE"
}

wait_for_service() {
    local cluster_name
    local service_name

    cluster_name="$(stack_output ClusterName)"
    service_name="$(stack_output ServiceName)"

    aws ecs wait services-stable \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$REGION"
}

smoke_test_url() {
    local app_url
    app_url="$(stack_output LoadBalancerUrl)"

    for attempt in {1..18}; do
        if curl -fsS "${app_url}${HEALTH_CHECK_PATH}" >/dev/null 2>&1; then
            echo "Smoke test passed: ${app_url}${HEALTH_CHECK_PATH}"
            return
        fi
        sleep 10
    done

    echo "Smoke test failed: ${app_url}${HEALTH_CHECK_PATH}"
    exit 1
}

print_summary() {
    echo
    echo "Separate eval app deployed"
    echo "Stack:      $STACK_NAME"
    echo "Image:      ${EVAL_ECR_URI}:${IMAGE_TAG}"
    echo "App URL:    $(stack_output LoadBalancerUrl)"
    echo "Dashboard:  $(stack_output DashboardUrl)"
    echo "Log group:  $(stack_output LogGroupName)"
}

show_status() {
    if ! stack_exists; then
        echo "Stack not found: $STACK_NAME"
        return
    fi

    echo "Stack: $STACK_NAME ($(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text))"
    echo "App URL: $(stack_output LoadBalancerUrl)"
    aws ecs describe-services \
        --cluster "$(stack_output ClusterName)" \
        --services "$(stack_output ServiceName)" \
        --region "$REGION" \
        --query 'services[0].{Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount,TaskDefinition:taskDefinition}' \
        --output table
}

deploy() {
    ensure_prerequisites
    discover_default_network
    ensure_ecr_repository
    ensure_source_bucket
    ensure_codebuild_role
    package_source_bundle
    upload_source_bundle
    put_codebuild_project
    run_remote_build
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
    *)
        echo "Usage: bash scripts/deploy_eval_app.sh [deploy|status]"
        exit 1
        ;;
esac

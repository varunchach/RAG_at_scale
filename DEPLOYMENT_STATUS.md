# AWS Deployment Status

This file tracks the live state of the two AWS deployments created from this repository.

## Live Stacks

### Baseline App

- stack: `rag-at-scale`
- ECS service: `rag-at-scale-service`
- ALB URL: `http://rag-at-LoadB-k9sgizKB39xs-1241722479.us-east-1.elb.amazonaws.com`
- dashboard: `rag-at-scale-observability`
- purpose: stable baseline app without eval scoring enabled

### Eval App

- stack: `rag-at-scale-eval`
- ECS service: `rag-at-scale-eval-service`
- ALB URL: `http://rag-at-LoadB-ompcrYxiAh4f-372850274.us-east-1.elb.amazonaws.com`
- dashboard: `rag-at-scale-eval-observability`
- metric namespace: `RAGAtScaleEval/Application`
- purpose: isolated eval app with asynchronous LLM-as-judge scoring enabled

## Current Health

At the latest verification point:

- baseline stack: `CREATE_COMPLETE`
- eval stack: `CREATE_COMPLETE`
- baseline ECS service: steady state with `1/1` task running
- eval ECS service: steady state with `1/1` task running
- both ALB URLs responded successfully

## AWS Configuration

- region: `us-east-1`
- account id: `593755927741`
- default VPC: `vpc-0e0318f7665ce160e`
- public subnets:
  - `subnet-0f0b03dad65cdb844`
  - `subnet-0ac60f15c5b2310ae`
  - `subnet-00bb4338053a9dece`
  - `subnet-0baef118b484d6f99`
  - `subnet-0372bd0af3868d46f`
  - `subnet-0504ddee11f65813d`

## Images

### Baseline Image

- ECR repo: `rag-at-scale-service`
- typical image URI: `593755927741.dkr.ecr.us-east-1.amazonaws.com/rag-at-scale-service:latest`

### Eval Image

- ECR repo: `rag-at-scale-eval-service`
- built remotely through AWS CodeBuild on native `amd64`
- deployed from `docker/Dockerfile.eval` and `buildspec.eval.yml`

## Infrastructure Template

Primary infrastructure template:

- `cloudformation/ecs-fargate-alb.yaml`

That template now supports both:

- standard operational widgets
- eval-specific CloudWatch widgets when the eval flags are enabled

## Operational Notes

The repository is intentionally set up so the eval app does not replace the baseline app.

Safety rules:

1. baseline and eval apps use different stack names
2. baseline and eval apps use different ECR repos
3. the eval app has its own ALB, ECS service, log group, and dashboard
4. the baseline app remains the safe fallback for live demos

## Useful Commands

Baseline deploy:

```bash
bash scripts/deploy_aws.sh
```

Baseline status:

```bash
bash scripts/deploy_aws.sh status
```

Eval deploy:

```bash
bash scripts/deploy_eval_app.sh deploy
```

Eval status:

```bash
bash scripts/deploy_eval_app.sh status
```

## Recommended Companion Docs

- `README.md`
- `SETUP.md`
- `docs/APP_ASSEMBLY_GUIDE.md`
- `docs/NEXUS_SAMPLE_QA.md`

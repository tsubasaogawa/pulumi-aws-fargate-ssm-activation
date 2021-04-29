# pulumi-aws-fargate-ssm-activation

A sample script to create fargate with ssm activation using Pulumi

## Resources to be created

- Networks
  - VPC
  - Subnet
  - Internet Gateway
  - Security Group
  - Route Table
- IAM
  - Role
  - Policy
- ECS
  - Cluster
  - Service
  - Task Definition
- ECR
  - Repository
- CloudWatch
  - Log Group
- SSM
  - Activation

## How to use

### Create environment

```bash
pulumi up
```

### Push a sample container

```bash
cd ssm_agent_image

docker build -t <your aws account id>.dkr.ecr.ap-northeast-1.amazonaws.com/fargate-ssm-activation-repository:latest .
docker push <your aws account id>.dkr.ecr.ap-northeast-1.amazonaws.com/fargate-ssm-activation-repository:latest
```

### Login to fargate

```bash
# Target id can be seen in CloudWatch Logs
aws ssm start-session --target mi-*** --region ap-northeast-1

Starting session with SessionId: tsubasa_ogawa-0f33bd24bf7dd3d84
$ uname -a
Linux 4bad4f403079462c89330736a4290ce4-2321958336 4.14.225-168.357.amzn2.x86_64 #1 SMP Mon Mar 15 18:00:02 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux
```

### Destroy environment

```bash
pulumi destroy
```

## Specification of sample container

- SSM-Agent plugin is installed
- Login via SSM-Agent using environment variables (ACTIVATION_CODE, ACTIVATION_ID, REGION)
- Container does not stop until we forcibly stop from ECS management console
  - `while :; do sleep 1; done` is written in entrypoint script

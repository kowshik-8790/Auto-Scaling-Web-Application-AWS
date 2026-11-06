# Auto Scaling Web Application on AWS (EC2, ALB, Auto Scaling, CloudWatch)

![AWS Architecture](https://img.shields.io/badge/AWS-EC2%20%7C%20ALB%20%7C%20AutoScaling%20%7C%20CloudWatch-FF9900?logo=amazon-aws&logoColor=white)
![IaC](https://img.shields.io/badge/IaC-CloudFormation%20%7C%20Terraform-blue)
![Python](https://img.shields.io/badge/Language-Python%20%7C%20Flask%20%7C%20Gunicorn-3776AB?logo=python&logoColor=white)

A high-availability, fault-tolerant cloud architecture demonstrating automated horizontal elasticity on Amazon Web Services. Incorporates an **Application Load Balancer (ALB)** distributing traffic across multi-AZ **Amazon EC2** Linux instances managed by an **Auto Scaling Group (ASG)** with **Amazon CloudWatch** metrics and target tracking policies.

---

## Architecture Overview

```text
                           +---------------------------+
                           |       Client Traffic      |
                           +-------------+-------------+
                                         |
                                (HTTP Port 80)
                                         |
                                         v
                           +-------------+-------------+
                           | Application Load Balancer |
                           |  (Multi-AZ Public Subnet) |
                           +-------------+-------------+
                                         |
                        +----------------+----------------+
                        |                                 |
           (Target Group Health Check)        (Target Group Health Check)
                        |                                 |
                        v                                 v
            +-----------+-----------+         +-----------+-----------+
            |      EC2 Instance     |         |      EC2 Instance     |
            | (Availability Zone A) |         | (Availability Zone B) |
            |    [Flask / Gunicorn] |         |    [Flask / Gunicorn] |
            +-----------+-----------+         +-----------+-----------+
                        ^                                 ^
                        |                                 |
                        +----------------+----------------+
                                         |
                        +----------------+----------------+
                        |      Auto Scaling Group         |
                        |      (Min: 2, Max: 6)           |
                        +----------------+----------------+
                                         |
                        +----------------+----------------+
                        |     Amazon CloudWatch Alarm     |
                        | (CPU Utilization > 50% Trigger) |
                        +---------------------------------+
```

### Traffic & Autoscaling Flow:
1. **Application Load Balancer (ALB)** accepts client HTTP traffic on port 80 across two separate Availability Zones.
2. **Target Group Health Probes** continuously poll `/health` every 20 seconds. Traffic is routed exclusively to healthy EC2 instances.
3. **IMDSv2 Instance Telemetry**: Each Flask instance fetches and displays its Instance ID, Availability Zone, and private IP so round-robin load distribution can be observed on refresh.
4. **Target Tracking Scaling Policy**: CloudWatch tracks `ASGAverageCPUUtilization`. When average CPU exceeds **50%**, the Auto Scaling Group provisions new EC2 instances (scale-out). When load subsides, excess instances are cleanly terminated (scale-in).

---

## Security & Network Isolation

- **Security Group Chaining (Least Privilege)**:
  - `ALB Security Group`: Inbound HTTP port 80 from `0.0.0.0/0`.
  - `EC2 Security Group`: Inbound HTTP port 80 restricted **strictly** to the ALB Security Group ID (`SourceSecurityGroupId`). Direct public HTTP bypass to EC2 instances is blocked.
- **IMDSv2 Enforced**: EC2 Launch Template enforces `HttpTokens: required` with a hop limit of 2, preventing SSRF credential extraction.
- **Systemd Daemon Isolation**: Web app runs as a managed background service via Gunicorn under `aws-webapp.service`.

---

## Repository Structure

```text
aws-auto-scaling-web-app/
│
├── app/
│   ├── app.py                     # Flask web app with IMDSv2 metadata & stress endpoint
│   ├── templates/index.html       # Live telemetry dashboard & interactive stress trigger
│   ├── requirements.txt           # Dependencies (Flask, requests, psutil, gunicorn)
│   └── aws-webapp.service         # Systemd service unit configuration
│
├── infrastructure/
│   ├── cloudformation.yaml        # Full VPC, ALB, ASG, CloudWatch CloudFormation template
│   └── terraform/                 # Complete Terraform configuration
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── scripts/
│   ├── stress_test.py             # Concurrency and CPU load generator
│   └── health_probe.sh            # Real-time multi-AZ target health prober
│
└── README.md
```

---

## Deployment Guide

### Option A: AWS CloudFormation Deployment (Recommended)

1. **Deploy the Stack**:
   ```bash
   aws cloudformation deploy \
     --template-file infrastructure/cloudformation.yaml \
     --stack-name production-autoscaling-app \
     --parameter-overrides ProjectName=asg-webapp InstanceType=t3.micro \
     --capabilities CAPABILITY_IAM
   ```

2. **Retrieve Application Endpoint**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name production-autoscaling-app \
     --query "Stacks[0].Outputs[?OutputKey=='ApplicationURL'].OutputValue" \
     --output text
   ```

3. **Open the Output URL** in your browser to view the live dashboard.

---

### Option B: HashiCorp Terraform Deployment

1. **Initialize and Deploy**:
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform apply -auto-approve
   ```

2. **Retrieve Output**:
   ```bash
   terraform output application_url
   ```

---

## Testing & Verifying Auto Scaling

### 1. Verify Multi-AZ Load Balancing
Run the automated probe script or refresh your browser:
```bash
./scripts/health_probe.sh http://YOUR_ALB_DNS_NAME
```
*Notice the serving `instance_id` and `availability_zone` alternating between AZ-A and AZ-B.*

### 2. Trigger CloudWatch Alarm & Scale-Out
Run the stress test tool to generate concurrent traffic and CPU load:
```bash
python ./scripts/stress_test.py http://YOUR_ALB_DNS_NAME 120 30
```
- Or click the **"Trigger 90s CPU Stress Load"** button directly on the web app UI.
- Watch **AWS CloudWatch Metrics** (`ASGAverageCPUUtilization`) exceed 50%.
- Check the **Auto Scaling Group Activity History** in AWS Console:
  ```text
  Activity: "At 2026-11-06... an instance was started in response to a difference between desired and actual capacity."
  Capacity expands from 2 -> 3 -> 4 instances.
  ```

---

## Author

**Kasanaboina Kowshik**  
- **Role:** Aspiring AWS Cloud Engineer  
- **GitHub:** [@kowshik-8790](https://github.com/kowshik-8790)  
- **LinkedIn:** [linkedin.com/in/kasanaboina-kowshik](https://linkedin.com/in/kasanaboina-kowshik)  
- **Email:** kasanaboinakowshik@gmail.com

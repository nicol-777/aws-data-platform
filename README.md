# AWS Serverless Data Platform

A production-style cloud data platform built on AWS, demonstrating end-to-end data engineering across ingestion, validation, trusted data access, monitoring, and automated deployment.

---

## Architecture

```
S3 (raw/)
    ↓  S3 event trigger
Lambda — data-validation-function
    ↓                    ↓
S3 (trusted/)      S3 (quarantine/)
    ↓                    ↓
API Gateway          SNS Alert → Email
    ↓
trusted-data-api Lambda
    ↓
External consumer (secured via API Key)

DynamoDB ← audit log written on every validation event

GitHub Actions → auto-deploys Lambda on every push
```

---

## Features

- **Event-driven validation** — Lambda automatically triggers when files land in `raw/`, enforcing business rules before data is promoted
- **Trusted data zones** — S3 is structured into `raw/`, `trusted/`, and `quarantine/` layers, mirroring enterprise data lake design
- **Secured REST API** — API Gateway exposes trusted data via a `GET /data` endpoint, protected by API Key authentication and rate limiting
- **Audit logging** — Every validation event is written to DynamoDB with file name, timestamp, result, issues, and destination
- **Alerting** — SNS publishes email alerts when data fails validation and is quarantined
- **Monitoring** — CloudWatch logs all API requests with a dashboard tracking request count, error rates, and latency
- **Infrastructure as Code** — Core AWS resources are defined in Terraform for reproducibility
- **CI/CD** — GitHub Actions automatically deploys Lambda functions to AWS on every push to `main`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Cloud | AWS |
| Compute | AWS Lambda (Python 3.12) |
| Storage | AWS S3 |
| Database | AWS DynamoDB |
| API | AWS API Gateway (REST) |
| Alerting | AWS SNS |
| Monitoring | AWS CloudWatch |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Data processing | Pandas |

---

## Project Structure

```
aws-data-platform/
├── lambda/
│   ├── data_validation.py       # Validates raw data, routes to trusted/ or quarantine/
│   └── trusted_data_api.py      # Reads trusted data from S3, returns as JSON via API
├── main.tf                      # Terraform — defines S3, DynamoDB, SNS resources
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions CI/CD pipeline
└── .gitignore
```

---

## Data Validation Rules

The validation Lambda enforces the following business rules on every file uploaded to `raw/`:

| Rule | Action on failure |
|---|---|
| No negative values in `value` column | Route to `quarantine/`, send SNS alert |
| No records with `last_updated` older than 30 days | Route to `quarantine/`, send SNS alert |
| All rules pass | Route to `trusted/`, log result to DynamoDB |

---

## API

### Endpoint
```
GET https://<api-id>.execute-api.eu-north-1.amazonaws.com/prod/data
```

### Authentication
All requests must include a valid API key in the header:
```
x-api-key: <your-api-key>
```

### Rate Limiting
- 10 requests per second
- Burst of 20
- 1,000 requests per day

### Example Response
```json
[
  {"user_id": 101, "asset": "AAPL", "value": 15000, "last_updated": "2026-03-09"},
  {"user_id": 102, "asset": "TSLA", "value": 20000, "last_updated": "2026-03-09"},
  {"user_id": 105, "asset": "GOOG", "value": 12000, "last_updated": "2026-03-09"}
]
```

---

## DynamoDB Audit Log

Every validation event is logged to the `data-validation-logs` table:

| Attribute | Description |
|---|---|
| `file_name` | Name of the processed file |
| `timestamp` | ISO 8601 timestamp of processing |
| `result` | `PASSED` or `FAILED` |
| `issues` | List of validation failures, or `None` |
| `destination` | `trusted` or `quarantine` |

---

## CI/CD Pipeline

Every push to `main` triggers a GitHub Actions workflow that:

1. Checks out the repository
2. Configures AWS credentials from GitHub Secrets
3. Packages and deploys `data-validation-function` Lambda
4. Packages and deploys `trusted-data-api` Lambda

AWS credentials are stored securely as GitHub repository secrets and never exposed in code.

---

## Infrastructure as Code

Core infrastructure is defined in `main.tf` using Terraform:

```bash
terraform init
terraform plan
terraform apply
```

Resources managed:
- S3 bucket
- DynamoDB table
- SNS topic

---

## Key Engineering Decisions

- **Serverless architecture** — Zero infrastructure management, automatic scaling, pay-per-use
- **Separation of concerns** — Validation logic is decoupled from API serving logic across two independent Lambda functions
- **Trust-based routing** — Data is never served from `raw/` — consumers only access data that has passed validation
- **Immutable audit trail** — DynamoDB logs are append-only, providing full lineage of every file processed
- **Secure by default** — API endpoint returns `403 Forbidden` without a valid API key

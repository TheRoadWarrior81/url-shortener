# URL Shortener

A serverless URL shortener built on AWS. Paste a long URL, get a short one, track how many times it's been clicked.

**Live:** [short.pranav-main-bucket-1.click](https://short.pranav-main-bucket-1.click)

---

## Architecture

![Architecture diagram](docs/architecture.png)

## What it does

- Shortens any valid URL to a 6-character alias
- Redirects short links to their original destination
- Tracks click counts per short link
- Serves a React frontend over HTTPS via a custom domain

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) |
| Hosting | S3 + CloudFront + Route 53 |
| API | AWS API Gateway (HTTP API v2) |
| Compute | AWS Lambda (Python 3.12) |
| Database | DynamoDB (on-demand) |
| IaC | Terraform |
| TLS | AWS Certificate Manager |

---

## Architecture

Three Lambda functions sit behind API Gateway:

- **`POST /shorten`** — validates the URL, generates a unique 6-character ID with collision checking, stores it in DynamoDB
- **`GET /{short_id}`** — looks up the original URL, increments the click counter, returns a 301 redirect
- **`GET /stats/{short_id}`** — returns the original URL and current click count

The React frontend is deployed to S3 and served via CloudFront with a custom subdomain (`short.pranav-main-bucket-1.click`). CloudFront uses an Origin Access Control (OAC) policy so the S3 bucket remains private.

---

## Project structure

```
url-shortener/
├── terraform/
│   ├── main.tf          # DynamoDB, IAM, Lambda, API Gateway
│   ├── frontend.tf      # S3, CloudFront, ACM, Route 53, stats Lambda
│   ├── variables.tf
│   ├── outputs.tf
│   └── lambda/
│       ├── shorten.py
│       ├── redirect.py
│       └── stats.py
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   └── App.css
    └── .env.production
```

---

## Local development

**Prerequisites:** Node 18+, Python 3.12, Terraform 1.5+, AWS CLI configured

```bash
# Frontend
cd frontend
npm install
npm run dev

# Terraform (from terraform/)
terraform init
terraform plan
terraform apply
```

---

## Deploy

```bash
# 1. Apply infrastructure
cd terraform && terraform apply

# 2. Build and upload frontend
cd ../frontend && npm run build
aws s3 sync dist/ s3://$(cd ../terraform && terraform output -raw frontend_bucket) --delete

# 3. Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(cd ../terraform && terraform output -raw cloudfront_id) \
  --paths "/*"
```

---

## Design decisions

**Why DynamoDB?** The access pattern is almost entirely single-item lookups by `short_id` — a hash key lookup is O(1) and costs nothing at low traffic with on-demand billing.

**Why Lambda over a server?** URL shorteners are read-heavy but bursty. Lambda scales to zero when idle and handles spikes without provisioning.

**Why CloudFront in front of S3?** The S3 bucket stays private (no public access). CloudFront handles HTTPS termination, caching, and the custom domain — and the OAC policy ensures only CloudFront can read the bucket.

**Short ID collision handling:** The shorten Lambda generates a random 6-character alphanumeric ID (~56 billion possibilities), checks DynamoDB for existence, and retries up to 3 times if there's a collision. At current scale this is effectively never needed, but it's the correct approach.

---

## Known limitations / future improvements

- No duplicate URL detection — shortening the same URL twice creates two entries (would require a GSI on `original_url`)
- No link expiry / TTL
- Click count is only refreshed on demand (no real-time updates)
- No authentication — anyone can shorten URLs

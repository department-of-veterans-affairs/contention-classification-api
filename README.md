# Contention Classification API

[![Build and Push to ECR](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/build_and_push_to_ecr.yml/badge.svg?event=push)](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/build_and_push_to_ecr.yml)
[![Continuous Integration](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/continuous-integration.yml)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
![Python Version](https://img.shields.io/badge/Python-3.12-blue)

Maps contention text and diagnostic codes from 526 submissions to contention classification codes as defined in the [Benefits Reference Data API](https://developer.va.gov/explore/benefits/docs/benefits_reference_data).

## Quick Start

**Prerequisites:** Python 3.12.3, Poetry, AWS credentials

### Setup & Run
```bash
# Install dependencies
poetry install

# Configure AWS (choose one)
aws configure
# OR set environment variables:
# export AWS_ACCESS_KEY_ID=your_key AWS_SECRET_ACCESS_KEY=your_secret AWS_DEFAULT_REGION=us-gov-west-1

# Install pre-commit hooks
poetry run pre-commit install

# Start the service
poetry run uvicorn python_src.api:app --port 8120 --reload
# OR with Docker: docker compose up --build

# Test it works
curl http://localhost:8120/health
```

## API Usage

**Documentation:** `http://localhost:8120/docs`

### Endpoints
- `/health` - Health check
- `/expanded-contention-classification` - Full classification with claim tracking
- `/ml-contention-classification` - ML-only classification
- `/hybrid-contention-classification` - Hybrid ML + rule-based classification

### Example Request
```bash
curl -X POST 'http://localhost:8120/expanded-contention-classification' \
  -H 'Content-Type: application/json' \
  -d '{
    "claim_id": 44,
    "contentions": [{
      "contention_text": "PTSD (post-traumatic stress disorder)",
      "contention_type": "NEW"
    }]
  }'
```

## Testing & Development

```bash
# Run tests
poetry run pytest

# For local ML development
# 1. Download model from VA SharePoint (see link in Configuration)
# 2. Update app_config.yaml with local file path
# Note: .pkl files are dev-only, production uses ONNX
```

## Configuration

### Environment Variables
- `ML_MODEL_SHA256` - Model file checksum
- `ML_VECTORIZER_SHA256` - Vectorizer file checksum
- `DISABLE_SHA_VERIFICATION=true` - Disable checksum verification (dev only)

### ML Model Setup
- **Local Dev:** Download from [VA SharePoint](https://dvagov.sharepoint.com/:f:/r/sites/vaabdvro/Shared%20Documents/Contention%20Classification/4%20-%20Data%20Discovery/CAIO%20Collaboration%20Documentation/model_6_2_25)
- **Production:** Uses ONNX format with S3 + SHA-256 verification

## Deployment

- **dev/staging:** Auto-deploy on `main` branch
- **sandbox/prod:** Manual via [release workflow](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/release.yml)
- **Config:** Managed via [`vsp-infra-application-manifests`](https://github.com/department-of-veterans-affairs/vsp-infra-application-manifests)

## Troubleshooting

**Common fixes:**
- Poetry errors → Run from project root with `pyproject.toml`
- Service issues → `pkill -f uvicorn && tail -40 nohup.out`
- AWS issues → Verify credentials and `AWS_DEFAULT_REGION=us-gov-west-1`
- Model errors → Check S3 permissions and SHA-256 checksums

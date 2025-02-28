# Contention Classification

[![Build and Push to ECR](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/build_and_push_to_ecr.yml/badge.svg?event=push)](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/build_and_push_to_ecr.yml)
[![Continuous Integration](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/continuous-integration.yml)
[![Maintainability](https://api.codeclimate.com/v1/badges/e48f6ba9d97c1ff3ecab/maintainability)](https://codeclimate.com/github/department-of-veterans-affairs/contention-classification-api/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/e48f6ba9d97c1ff3ecab/test_coverage)](https://codeclimate.com/github/department-of-veterans-affairs/contention-classification-api/test_coverage)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
![Python Version from PEP 621 TOML](https://img.shields.io/badge/Python-3.12-blue)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

`/contention-classification/va-gov-claim-classifier` maps contention text and diagnostic codes from 526 submission to contention classification codes as defined in the [Benefits Reference Data API](https://developer.va.gov/explore/benefits/docs/benefits_reference_data).

## Getting started

This service can be run standalone using Poetry for dependency management or using Docker.

## Setup

### Python using Poetry

#### Install Python 3.12.3

Mac Users: you can use pyenv to handle multiple python versions

```bash
brew install pyenv
pyenv install 3.12.3 #Installs latest version of python 3.12.3
pyenv global 3.12.3 # or don't do this if you want a different version available globally for your system
```

Mac Users: If python path hasn't been setup, you can put the following in your ~/.zshrc

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:$PATH"
if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi" #Initalize pyenv in current shell session
```

#### Install Poetry

This project uses [Poetry](https://python-poetry.org/docs/) to manage dependencies.

Follow the directions on the [Poetry website](https://python-poetry.org/docs/#installation) for installation:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Install dependencies

Use Poetry to install all dependencies:

```bash
poetry install
```

#### Install pre-commit hooks

```bash
poetry run pre-commit install
```

To run the pre-commit hooks manually:

```bash
poetry run pre-commit run --all-files
```

### Run the server

Using Poetry, run the FastAPI server:

```bash
poetry run uvicorn python_src.api:app --port 8120 --reload
```

### Run tests

Using Poetry, run the test suite:

```bash
poetry run pytest
```

For test coverage report:

```bash
poetry run pytest --cov=src --cov-report=term-missing
```

## Running with Docker
This application can also be run with Docker using the following commands.
```
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Testing locally
With the application running using either Docker or Python, tests requests can be sent using the following curl commands.

To test the health of the application or to check if the application is running at the `contention-classification/health` endpoint:
```
curl -X 'GET' 'http://localhost:8120/health'
```

To test the classification provided at the `contention-classification/va-gov-claim-classifier` endpoint:

```
curl -X 'POST'   'http://localhost:8120/va-gov-claim-classifier'   -H 'accept: application/json'   -H 'Content-Type: application/json'   -d '{
  "claim_id": 44,
  "form526_submission_id": 55,
  "contentions": [
        {
            "contention_text": "PTSD (post-traumatic stress disorder)",
            "contention_type": "NEW"
        },
        {
            "contention_text": "acl tear, right",
            "contention_type": "NEW"
        },
        {
            "contention_text": "",
            "contention_type": "INCREASE",
            "diagnostic_code": 5012
        }
    ]
}'
```

To test the classification provided by the experimental endpoint at `contention-classification/expanded-contention-classification`:
```
curl -X 'POST'   'http://localhost:8120/expanded-contention-classification'   -H 'accept: application/json'   -H 'Content-Type: application/json'   -d '{
  "claim_id": 44,
  "form526_submission_id": 55,
  "contentions": [
        {
            "contention_text": "PTSD (post-traumatic stress disorder)",
            "contention_type": "NEW"
        },
        {
            "contention_text": "acl tear, right",
            "contention_type": "NEW"
        },
        {
            "contention_text": "",
            "contention_type": "INCREASE",
            "diagnostic_code": 5012
        }
    ]
}'
```

An alternative to the above `curl` commands is to use a local testing application like [Bruno](https://www.usebruno.com/) or [Postman](https://www.postman.com/).  Different JSON request bodies can be set up for testing each of the above endpoints and tests can be saved using Collections within these tools.


## Building docs

API Documentation is automatically created by FastAPI. This can be viewed by visiting `localhost:8120/docs` while the application is running.

For exporting the open API spec:

```bash
poetry run python src/python_src/pull_api_documentation.py
```

<!--
# TODO: add docker config https://github.com/department-of-veterans-affairs/abd-vro/issues/3895
## Docker

### Build and run with Docker Compose

```bash
docker compose up --build
```

### Run tests in Docker

```bash
docker compose run --rm api poetry run pytest
```

### Clean up Docker resources

```bash
docker compose down
docker system prune
docker volume prune
``` -->

## Deploying to VA Platform
### Building the image and publishing to ECR
Images are built and pushed to ECR using the [build_and_push_to_ecr.yml](.github/workflows/build_and_push_to_ecr.yml) workflow which is triggered in one of two ways:
* Automatically: when pushed when changes are pushed to the `main` branch, which should only be done when a Pull Request is merged into the `main` branch
* Manually: by triggering the action in [Github](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/build_and_push_to_ecr.yml)

This workflow is not triggered when changes are pushed to any branch other than the `main` branch.

### Deploying the image
The image is released to the VA Platform using the [release.yml](.github/workflows/release.yml) workflow which is triggered when a new image is pushed to ECR.
This workflow will deploy the latest image to the VA Platform automatically for the `dev` and `staging` environments.
The `sandbox` and `prod` environments must be deployed manually by triggering the action in [Github](https://github.com/department-of-veterans-affairs/contention-classification-api/actions/workflows/release.yml) and selecting the desired environment(s).

Note that manually triggering the deployment will deploy the most recent commit hash to the selected environment(s).

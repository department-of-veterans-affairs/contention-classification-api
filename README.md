# Contention Classification
`/contention-classification/va-gov-claim-classifier` maps contention text and diagnostic codes from 526 submission to classifications as defined in the [Benefits Reference Data API](https://developer.va.gov/explore/benefits/docs/benefits_reference_data).

## Getting started
This service can be run standalone using Poetry for dependency management.

## Setup
Install Python 3.11
Mac Users: you can use pyenv to handle multiple python versions
```
brew install pyenv
pyenv install 3.11 #Installs latest version of python 3.11
pyenv global 3.11 # or don't do this if you want a different version available globally for your system, set locally to use python in current folder.
```

Mac Users: If python path hasn't been setup, you can put the following in your ~/.zshrc
```
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:$PATH"
if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi" #Initalize pyenv in current shell session
```

Install Poetry and set up the project:
```
curl -sSL https://install.python-poetry.org | python3 -
poetry install
```

Run the FastAPI server:
```
poetry run uvicorn python_src.api:app --port 8120 --reload
```

## Unit tests
Pytest is used for Python Unit tests:
```
poetry run pytest
```

## Contributing
### Install pre-commit hooks
```
poetry install
pre-commit install
```

## Building docs
API Documentation is automatically created by FastAPI. This can be viewed at the /docs (e.g. localhost:8080/docs)
For exporting the open API spec and using documentation elsewhere, see [pull_api_documentation.py](https://github.com/department-of-veterans-affairs/abd-vro/blob/79bad1e34c98bada6dcfebe216820e52f4666df7/domain-cc/cc-app/src/python_src/util/pull_api_documentation.py)

## Docker
### Build and run with Docker Compose
```
docker-compose up --build
```

### Clean up Docker resources
```
docker-compose down
docker system prune
docker volume prune
```

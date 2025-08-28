"""
This standalone script pulls the OpenAPI specification of the FastAPI app and exports it to a JSON file.
This can be used to move the Swagger documentation to other tools, like a java project.

Usage:
    poetry run python src/util/pull_api_documentation.py

The script will generate a fastapi.json file containing the OpenAPI specification.
"""

import json

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def export_openapi(app: FastAPI, filename: str) -> None:
    """Export the OpenAPI specification of a FastAPI app to a JSON file."""
    openapi_schema = get_openapi(title=app.title, version=app.version, routes=app.routes)

    with open(filename, "w") as outfile:
        json.dump(openapi_schema, outfile, indent=4)


if __name__ == "__main__":
    from api import app

    export_openapi(app, "fastapi.json")
    print("Done!")

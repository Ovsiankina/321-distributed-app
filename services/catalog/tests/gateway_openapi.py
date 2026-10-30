"""Réponses catalog validées contre docs/api/gateway.openapi.yaml (contrat E1-05)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import jsonschema
from prance import ResolvingParser

REPO_ROOT = Path(__file__).resolve().parents[3]
GATEWAY_OPENAPI = REPO_ROOT / "docs/api/gateway.openapi.yaml"


@lru_cache(maxsize=1)
def gateway_spec() -> dict:
    parser = ResolvingParser(str(GATEWAY_OPENAPI))
    return parser.specification


def response_json_schema(path: str, method: str = "get", status: str = "200") -> dict:
    operation = gateway_spec()["paths"][path][method.lower()]
    return operation["responses"][status]["content"]["application/json"]["schema"]


def assert_matches_gateway_schema(
    instance: object,
    path: str,
    method: str = "get",
    status: str = "200",
) -> None:
    schema = response_json_schema(path, method, status)
    jsonschema.validate(instance=instance, schema=schema)

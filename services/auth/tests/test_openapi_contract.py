from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

from gateway_openapi import GATEWAY_OPENAPI, gateway_spec


def test_gateway_openapi_document_is_valid():
    spec, _ = read_from_filename(str(GATEWAY_OPENAPI))
    validate(spec)


def test_contract_lists_every_status_the_service_returns():
    paths = gateway_spec()["paths"]
    # 502 vient de la Gateway, pas d'Auth.
    assert set(paths["/api/auth/register"]["post"]["responses"]) == {
        "201",
        "400",
        "409",
        "502",
    }
    assert set(paths["/api/auth/login"]["post"]["responses"]) == {
        "200",
        "400",
        "401",
        "429",
        "502",
    }
    assert set(paths["/api/auth/me"]["get"]["responses"]) == {"200", "401", "502"}

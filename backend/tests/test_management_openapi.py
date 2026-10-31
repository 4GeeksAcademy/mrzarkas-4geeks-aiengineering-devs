import pytest

from app.main import app


@pytest.mark.parametrize(
    ("path", "method", "code", "response", "input_schema"),
    [
        ("/management/catalogs", "get", "200", "CatalogListResponse", None),
        ("/management/catalogs/{catalog_name}/values", "get", "200", "CatalogValueListResponse", None),
        ("/management/catalogs/{catalog_name}/values", "post", "201", "ManagedCatalogValueResponse", "CatalogValueCreate"),
        ("/management/catalogs/{catalog_name}/values/{value_id}", "patch", "200", "ManagedCatalogValueResponse", "CatalogValueUpdate"),
        ("/management/catalogs/{catalog_name}/values/{value_id}/activation", "post", "200", "ManagedCatalogValueResponse", "ActivationRequest"),
        ("/management/reference-data/{resource}", "get", "200", "ReferenceValueListResponse", None),
        ("/management/reference-data/{resource}", "post", "201", "ReferenceValueResponse", "ReferenceValueCreate"),
        ("/management/reference-data/{resource}/{resource_id}", "patch", "200", "ReferenceValueResponse", "ReferenceValueUpdate"),
        ("/management/reference-data/{resource}/{resource_id}/activation", "post", "200", "ReferenceValueResponse", "ActivationRequest"),
        ("/management/affected-systems/{system_id}/jurisdictions", "put", "200", None, "SystemJurisdictionsUpdate"),
        ("/management/audit-events", "get", "200", "ManagementAuditEventListResponse", None),
    ],
)
def test_management_routes_publish_existing_contracts(path, method, code, response, input_schema) -> None:
    operation = app.openapi()["paths"][path][method]
    schema = operation["responses"][code]["content"]["application/json"]["schema"]
    if response is None:
        assert schema["type"] == "array"
        assert schema["items"] == {"type": "string", "format": "uuid"}
    else:
        assert schema == {"$ref": f"#/components/schemas/{response}"}
    if input_schema:
        assert operation["requestBody"]["content"]["application/json"]["schema"] == {
            "$ref": f"#/components/schemas/{input_schema}"
        }
    if method == "get":
        parameters = {item["name"]: item["schema"] for item in operation["parameters"]}
        assert parameters["offset"]["minimum"] == 0
        assert parameters["limit"]["minimum"] == 1
        assert parameters["limit"]["maximum"] == 100


def test_catalog_value_list_has_dedicated_schema_with_unchanged_fields() -> None:
    schemas = app.openapi()["components"]["schemas"]
    list_schema = schemas["CatalogValueListResponse"]
    detail_schema = schemas["ManagedCatalogValueResponse"]
    item_schema = schemas["CatalogValueListItem"]

    assert set(list_schema["properties"]) == {"items", "total"}
    assert list_schema["properties"]["items"]["items"]["$ref"] == (
        "#/components/schemas/CatalogValueListItem"
    )
    assert item_schema["properties"] == detail_schema["properties"]
    assert item_schema["required"] == detail_schema["required"]


def test_reference_list_has_dedicated_schema_with_unchanged_fields() -> None:
    schemas = app.openapi()["components"]["schemas"]
    list_schema = schemas["ReferenceValueListResponse"]
    detail_schema = schemas["ReferenceValueResponse"]
    item_schema = schemas["ReferenceValueListItem"]

    assert set(list_schema["properties"]) == {"items", "total"}
    assert list_schema["properties"]["items"]["items"]["$ref"] == (
        "#/components/schemas/ReferenceValueListItem"
    )
    assert item_schema["properties"] == detail_schema["properties"]
    assert item_schema["required"] == detail_schema["required"]

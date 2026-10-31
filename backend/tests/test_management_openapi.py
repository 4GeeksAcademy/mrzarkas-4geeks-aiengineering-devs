from app.main import app


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
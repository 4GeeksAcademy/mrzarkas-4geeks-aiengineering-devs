from app.catalogs.schemas import CatalogResponse
from app.catalogs.seed import CATALOGS


def test_seed_contains_the_four_provisional_catalogs() -> None:
    assert set(CATALOGS) == {
        "entryChannel",
        "incidentType",
        "severity",
        "incidentStatus",
    }


def test_status_seed_preserves_open_state() -> None:
    statuses = {value[0]: value[2] for value in CATALOGS["incidentStatus"]}

    assert statuses["new"] is True
    assert statuses["onHold"] is True
    assert statuses["reopened"] is True
    assert statuses["resolved"] is False
    assert statuses["closed"] is False
    assert statuses["cancelled"] is False


def test_catalog_response_serializes_stable_keys() -> None:
    response = CatalogResponse(
        catalog_name="severity",
        version=1,
        values=[],
    )

    assert response.model_dump() == {
        "catalog_name": "severity",
        "version": 1,
        "values": [],
    }
import pytest

from biomcp import catalog


def test_catalog_is_registry_authoritative_and_deterministic():
    result = catalog()

    assert result["product"] == "BioMCP"
    assert result["schema_version"] == "1.3"
    assert [server["name"] for server in result["servers"]] == sorted(
        server["name"] for server in result["servers"]
    )

    imagej = next(server for server in result["servers"] if server["name"] == "imagej")
    assert imagej["status"] == "experimental"
    assert imagej["installable"] is True
    assert imagej["transport"] == ["stdio"]
    assert imagej["tools"] == ["imagej_status", "run_macro"]


def test_catalog_can_filter_one_registered_server():
    result = catalog("imagej")

    assert result["server_count"] == 1
    assert result["servers"][0]["name"] == "imagej"


def test_catalog_rejects_unknown_server():
    with pytest.raises(ValueError, match="Unknown BioMCP server: missing"):
        catalog("missing")

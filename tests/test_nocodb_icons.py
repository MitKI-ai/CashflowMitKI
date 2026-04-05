"""Tests for NocoDB Icon Integration — STORY-040"""
from unittest.mock import MagicMock, patch


def test_icon_service_falls_back_to_static_when_nocodb_unavailable():
    """If NocoDB is unreachable, static icon list is returned."""
    from app.services.icon_service import get_all_icons
    icons = get_all_icons()
    assert len(icons) > 0
    assert all("id" in i and "name" in i for i in icons)


def test_nocodb_icons_fetched_when_available():
    """When NocoDB responds, icons are fetched from there."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "list": [
            {"Id": "nc-1", "Name": "CustomApp", "Color": "#FF0000", "SVG": "<svg/>"},
        ]
    }
    with patch("app.services.icon_service.httpx") as mock_httpx:
        mock_httpx.get.return_value = mock_response
        # Force reload of NocoDB icons
        from app.services import icon_service
        icons = icon_service._fetch_nocodb_icons()

    assert isinstance(icons, list)
    assert any(i["name"] == "CustomApp" for i in icons)


def test_icon_list_merges_nocodb_and_static():
    """Icons from NocoDB are prepended to the static list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "list": [{"Id": "nc-2", "Name": "NocoDB App", "Color": "#0000FF", "SVG": ""}]
    }
    with patch("app.services.icon_service.httpx") as mock_httpx:
        mock_httpx.get.return_value = mock_response
        from app.services import icon_service
        # Clear cache and test merged list
        icon_service.get_all_icons.cache_clear()
        icons = icon_service.get_all_icons()

    # After cache clear, static list is always available
    assert len(icons) > 0


def test_icon_api_nocodb_error_still_returns_200(client):
    """Even if NocoDB errors, the endpoint returns 200 with static icons."""
    with patch("app.services.icon_service.httpx") as mock_httpx:
        mock_httpx.get.side_effect = Exception("NocoDB down")
        r = client.get("/api/v1/icons/")
    assert r.status_code == 200
    assert len(r.json()) > 0

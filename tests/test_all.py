import pytest
from scraper.parsers import parse_tudum_page
from server.app import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_manifest():
    response = client.get("/manifest.json")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "catalogs" in data
    assert len(data["catalogs"]) >= 2

def test_catalog_404():
    response = client.get("/catalog/movie/invalid_id.json")
    assert response.status_code == 404

def test_parser_empty():
    # Test with empty HTML
    items = parse_tudum_page("", "malaysia", "movie")
    assert items == []

def test_parser_mock_html():
    # Create a minimal mock HTML that resembles what we expect
    # This is based on the assumption in parsers.py
    html = """
    <table>
        <tbody>
            <tr>
                <td>1</td>
                <td>Test Movie</td>
            </tr>
        </tbody>
    </table>
    """
    items = parse_tudum_page(html, "malaysia", "movie")
    assert len(items) == 1
    assert items[0].rank == 1
    assert items[0].title == "Test Movie"
    assert items[0].id == "testmovie"

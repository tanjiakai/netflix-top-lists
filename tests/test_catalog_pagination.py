from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

def test_manifest_order_and_names():
    response = client.get("/manifest.json")
    assert response.status_code == 200
    data = response.json()
    catalogs = data["catalogs"]
    
    # Check order: Movie first, then Series
    assert catalogs[0]["type"] == "movie"
    assert catalogs[1]["type"] == "series"
    
    # Check names
    assert catalogs[0]["name"] == "Netflix: Top in Malaysia Today"
    assert catalogs[1]["name"] == "Netflix: Top in Malaysia Today"

def test_catalog_pagination():
    # Normal request
    response = client.get("/catalog/movie/malaysia_movies.json")
    assert response.status_code == 200
    
    # Paginated request
    response = client.get("/catalog/movie/malaysia_movies/skip=0.json")
    assert response.status_code == 200
    
    response = client.get("/catalog/movie/malaysia_movies/skip=5.json")
    assert response.status_code == 200

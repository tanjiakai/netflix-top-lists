"""
Integration test to verify TMDB poster URLs.
"""

from fastapi.testclient import TestClient
from server.app import app
import json

client = TestClient(app)

def test_tmdb_posters():
    """Verify catalog items use TMDB poster URLs"""
    response = client.get("/catalog/series/malaysia_tv.json")
    assert response.status_code == 200
    
    data = response.json()
    metas = data.get("metas", [])
    
    if metas:
        # Check for item with TMDB poster
        # "Delhi Crime" should have one
        delhi_crime = next((m for m in metas if "Delhi Crime" in m["name"]), None)
        if delhi_crime:
            print(f"[TEST] Found Delhi Crime: {delhi_crime['name']}")
            assert "poster" in delhi_crime, "Poster field should be present"
            poster = delhi_crime["poster"]
            print(f"[TEST] Poster URL: {poster}")
            
            assert "image.tmdb.org" in poster, f"Should use TMDB poster URL: {poster}"
            print("[OK] Uses TMDB poster URL")
        else:
            print("[WARN] Delhi Crime not found")
            
        # Check fallback item
        # "Kitab Sijjin" (movie) likely uses fallback
        
    response_movies = client.get("/catalog/movie/malaysia_movies.json")
    metas_movies = response_movies.json().get("metas", [])
    
    custom_item = next((m for m in metas_movies if not m["id"].startswith("tt")), None)
    if custom_item:
        print(f"[TEST] Found Fallback Item: {custom_item['name']}")
        assert "poster" in custom_item, "Poster field should be present"
        poster = custom_item["poster"]
        print(f"[TEST] Poster URL: {poster}")
        
        assert "nflximg.net" in poster or "netflix.com" in poster, f"Should use Netflix poster URL: {poster}"
        print("[OK] Uses Netflix poster URL (Fallback)")

if __name__ == "__main__":
    test_tmdb_posters()
    print("\n[SUCCESS] All tests passed!")

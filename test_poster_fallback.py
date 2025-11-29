"""
Integration test to verify poster fallback logic.
"""

from fastapi.testclient import TestClient
from server.app import app
import json

client = TestClient(app)

def test_poster_fallback():
    """Verify poster is omitted for IMDb IDs and included for custom IDs"""
    response = client.get("/catalog/series/malaysia_tv.json")
    assert response.status_code == 200
    
    data = response.json()
    metas = data.get("metas", [])
    
    if metas:
        # 1. Check item WITH IMDb ID (should NOT have poster)
        # We know "Delhi Crime" has an IMDb ID from previous tests
        delhi_crime = next((m for m in metas if "Delhi Crime" in m["name"]), None)
        if delhi_crime:
            print(f"[TEST] Found item with IMDb ID: {delhi_crime['name']} ({delhi_crime['id']})")
            assert delhi_crime["id"].startswith("tt"), "Should have IMDb ID"
            assert "poster" not in delhi_crime, "Poster should be OMITTED for IMDb items (Cinemeta priority)"
            print("[OK] Poster omitted for IMDb item")
        
        # 2. Check item WITHOUT IMDb ID (should HAVE poster)
        # We need to find one that failed TMDB lookup. 
        # Based on previous logs, "Kitab Sijjin and Illiyyin" failed.
        # Let's check movies catalog for that one.
        
    response_movies = client.get("/catalog/movie/malaysia_movies.json")
    metas_movies = response_movies.json().get("metas", [])
    
    custom_item = next((m for m in metas_movies if not m["id"].startswith("tt")), None)
    if custom_item:
        print(f"[TEST] Found item with Custom ID: {custom_item['name']} ({custom_item['id']})")
        assert "poster" in custom_item, "Poster should be INCLUDED for custom ID items (Fallback)"
        print("[OK] Poster included for custom ID item")
    else:
        print("[WARN] No custom ID items found to test fallback")

if __name__ == "__main__":
    test_poster_fallback()
    print("\n[SUCCESS] All tests passed!")

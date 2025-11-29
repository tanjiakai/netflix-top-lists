"""
Integration test to verify title cleaning and poster restoration.
"""

from fastapi.testclient import TestClient
from server.app import app
import json

client = TestClient(app)

def test_catalog_clean_titles_and_posters():
    """Verify catalog items have clean titles and posters"""
    response = client.get("/catalog/series/malaysia_tv.json")
    assert response.status_code == 200
    
    data = response.json()
    metas = data.get("metas", [])
    
    if metas:
        # Check for a known cleaned title
        # "Delhi Crime: Season 3" should be "Delhi Crime"
        delhi_crime = next((m for m in metas if "Delhi Crime" in m["name"]), None)
        if delhi_crime:
            print(f"[TEST] Found Delhi Crime: {delhi_crime['name']}")
            assert delhi_crime["name"] == "Delhi Crime", f"Title should be cleaned: {delhi_crime['name']}"
            print("[OK] Title is cleaned")
            
            assert "poster" in delhi_crime, "Poster field should be present"
            print("[OK] Poster field is present")
            
            assert delhi_crime["id"].startswith("tt"), f"Should have IMDb ID: {delhi_crime['id']}"
            print("[OK] Has IMDb ID")
        else:
            print("[WARN] Delhi Crime not found in top 10 (might have changed)")
            
        # Check first item generally
        first = metas[0]
        print(f"[TEST] First item: {first['name']}")
        assert "poster" in first, "Poster field should be present"
        assert not "Season" in first["name"], "Should not have Season suffix (if applicable)"

if __name__ == "__main__":
    test_catalog_clean_titles_and_posters()
    print("\n[SUCCESS] All tests passed!")

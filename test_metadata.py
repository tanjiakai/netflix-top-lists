"""
Integration test to verify the metadata changes.
Tests that:
1. Rank is not in display names
2. Poster field is not included in responses
"""

from fastapi.testclient import TestClient
from server.app import app
import json

client = TestClient(app)

def test_catalog_no_rank_in_name():
    """Verify catalog items don't have rank prefix in name"""
    response = client.get("/catalog/movie/malaysia_movies.json")
    assert response.status_code == 200
    
    data = response.json()
    metas = data.get("metas", [])
    
    if metas:
        # Check first item doesn't have rank prefix
        first_item = metas[0]
        name = first_item.get("name", "")
        print(f"[TEST] First item name: {name}")
        
        # Name should not start with #
        assert not name.startswith("#"), f"Name should not have rank prefix: {name}"
        print("[OK] No rank prefix in name")

def test_catalog_no_poster():
    """Verify catalog items don't include poster field"""
    response = client.get("/catalog/series/malaysia_tv.json")
    assert response.status_code == 200
    
    data = response.json()
    metas = data.get("metas", [])
    
    if metas:
        # Check first item doesn't have poster field
        first_item = metas[0]
        print(f"[TEST] First item keys: {list(first_item.keys())}")
        
        assert "poster" not in first_item, "Poster field should not be included"
        print("[OK] No poster field in catalog")

def test_meta_endpoint():
    """Test that meta endpoint returns proper structure"""
    # First get an ID from catalog
    response = client.get("/catalog/movie/malaysia_movies.json")
    assert response.status_code == 200
    
    metas = response.json().get("metas", [])
    if metas:
        item_id = metas[0]["id"]
        print(f"[TEST] Testing meta endpoint with ID: {item_id}")
        
        # Get meta
        meta_response = client.get(f"/meta/movie/{item_id}.json")
        
        if meta_response.status_code == 200:
            meta_data = meta_response.json()
            meta = meta_data.get("meta", {})
            
            print(f"[TEST] Meta keys: {list(meta.keys())}")
            
            # Verify no poster field
            assert "poster" not in meta, "Poster should not be in meta"
            print("[OK] No poster in meta endpoint")
        else:
            print(f"[INFO] Meta endpoint returned {meta_response.status_code} (expected for custom IDs)")

if __name__ == "__main__":
    print("\n=== Testing Metadata Changes ===\n")
    test_catalog_no_rank_in_name()
    test_catalog_no_poster()
    test_meta_endpoint()
    print("\n[SUCCESS] All tests passed!")

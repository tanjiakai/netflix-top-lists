"""
Test script to verify TMDB integration.
Run this with: python test_tmdb.py
"""

import os
from dotenv import load_dotenv
from scraper.tmdb_client import TMDBClient

# Load environment variables from .env file
load_dotenv()

def test_tmdb():
    # Check if API key is set
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("[FAIL] TMDB_API_KEY not set!")
        print("[INFO] Set it with: export TMDB_API_KEY=your_key  (or add to .env file)")
        return False
    
    print("[OK] TMDB_API_KEY is set")
    
    # Initialize client
    client = TMDBClient(api_key)
    print("[OK] TMDB Client initialized")
    
    # Test movie search
    print("\n[TEST] Testing movie search...")
    imdb_id = client.search_movie("The Shawshank Redemption")
    if imdb_id:
        print(f"[OK] Found IMDb ID: {imdb_id}")
    else:
        print("[FAIL] Failed to find IMDb ID for movie")
        return False
    
    # Test TV search
    print("\n[TEST] Testing TV search...")
    imdb_id = client.search_tv("Breaking Bad")
    if imdb_id:
        print(f"[OK] Found IMDb ID: {imdb_id}")
    else:
        print("[FAIL] Failed to find IMDb ID for TV show")
        return False
    
    print("\n[SUCCESS] All TMDB tests passed!")
    return True

if __name__ == "__main__":
    test_tmdb()

import requests
import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TMDBClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self.last_request_time = 0
        self.min_request_interval = 0.25  # 4 requests per second to stay under limit
        
    def _rate_limit(self):
        """Ensure we don't exceed TMDB rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """Search for a movie and return IMDb ID"""
        if not self.api_key:
            logger.warning("TMDB_API_KEY not set, skipping IMDb ID lookup")
            return None
            
        self._rate_limit()
        
        try:
            params = {
                "api_key": self.api_key,
                "query": title,
                "include_adult": "false"
            }
            if year:
                params["year"] = year
                
            response = requests.get(
                f"{self.base_url}/search/movie",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                # Get the first result's ID
                tmdb_id = data["results"][0]["id"]
                return self._get_imdb_id_from_tmdb_id(tmdb_id, "movie")
                
        except Exception as e:
            logger.error(f"Error searching for movie '{title}': {e}")
            
        return None
    
    def search_tv(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """Search for a TV show and return IMDb ID"""
        if not self.api_key:
            logger.warning("TMDB_API_KEY not set, skipping IMDb ID lookup")
            return None
            
        self._rate_limit()
        
        try:
            params = {
                "api_key": self.api_key,
                "query": title,
                "include_adult": "false"
            }
            if year:
                params["first_air_date_year"] = year
                
            response = requests.get(
                f"{self.base_url}/search/tv",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                # Get the first result's ID
                tmdb_id = data["results"][0]["id"]
                return self._get_imdb_id_from_tmdb_id(tmdb_id, "tv")
                
        except Exception as e:
            logger.error(f"Error searching for TV show '{title}': {e}")
            
        return None
    
    def _get_imdb_id_from_tmdb_id(self, tmdb_id: int, media_type: str) -> Optional[str]:
        """Get IMDb ID from TMDB ID"""
        self._rate_limit()
        
        try:
            endpoint = f"{self.base_url}/{media_type}/{tmdb_id}/external_ids"
            response = requests.get(
                endpoint,
                params={"api_key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            imdb_id = data.get("imdb_id")
            if imdb_id:
                logger.info(f"Found IMDb ID: {imdb_id} for TMDB ID: {tmdb_id}")
                return imdb_id
                
        except Exception as e:
            logger.error(f"Error getting IMDb ID from TMDB ID {tmdb_id}: {e}")
            
        return None

import requests
from .parsers import parse_flixpatrol_page
from .models import ScrapedItem
from .tmdb_client import TMDBClient
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Generate today's date in YYYY-MM-DD format
today = datetime.now().strftime("%Y-%m-%d")

SCRAPE_TARGETS = {
    "malaysia_tv": {
        "url": f"https://flixpatrol.com/top10/netflix/malaysia/{today}/",
        "type": "series",
        "region": "malaysia"
    },
    "malaysia_movies": {
        "url": f"https://flixpatrol.com/top10/netflix/malaysia/{today}/",
        "type": "movie",
        "region": "malaysia"
    }
}

def fetch_page(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""

import re

def clean_title(title: str) -> str:
    """
    Clean title by removing specific suffixes like 'Season X', 'Limited Series', etc.
    Only removes the part after the colon if it matches these patterns.
    """
    # Pattern to match ": Season X", ": Limited Series", etc.
    # We look for a colon, optional whitespace, then the specific keywords
    pattern = r":\s*(Season\s+\d+|Limited\s+Series|Volume\s+\d+|Part\s+\d+|Chapter\s+\d+).*"
    cleaned = re.sub(pattern, "", title, flags=re.IGNORECASE)
    return cleaned.strip()

def scrape_all() -> dict[str, list[dict]]:
    results = {}
    tmdb_client = TMDBClient()
    
    for key, config in SCRAPE_TARGETS.items():
        logger.info(f"Scraping {key} from {config['url']}")
        html = fetch_page(config['url'])
        if html:
            items = parse_flixpatrol_page(html, config['region'], config['type'])
            
            # Fetch IMDb IDs for each item
            for item in items:
                # Clean title first (remove "Season X" etc.)
                original_title = item.title
                item.title = clean_title(original_title)
                if item.title != original_title:
                    logger.info(f"Cleaned title: '{original_title}' -> '{item.title}'")
                
                logger.info(f"Looking up IMDb ID for: {item.title}")
                if config['type'] == 'series':
                    imdb_id, poster_path = tmdb_client.search_tv(item.title)
                else:
                    imdb_id, poster_path = tmdb_client.search_movie(item.title)
                
                if imdb_id:
                    item.imdb_id = imdb_id
                    logger.info(f"Found IMDb ID {imdb_id} for {item.title}")
                else:
                    logger.warning(f"No IMDb ID found for {item.title}, using custom ID")
                    
                if poster_path:
                    item.tmdb_poster = poster_path
                    logger.info(f"Found TMDB poster for {item.title}")
            
            results[key] = [item.model_dump() for item in items]
            logger.info(f"Found {len(items)} items for {key}")
        else:
            results[key] = []
            
    return results

if __name__ == "__main__":
    import json
    import os
    
    data = scrape_all()
    
    # Write directly to file with UTF-8 encoding to avoid shell redirection encoding issues (e.g. PowerShell UTF-16)
    output_file = "catalog.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Successfully wrote catalog to {output_file}")

import requests
from .parsers import parse_tudum_page
from .models import ScrapedItem
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRAPE_TARGETS = {
    "malaysia_tv": {
        "url": "https://www.netflix.com/tudum/top10/malaysia/tv",
        "type": "series",
        "region": "malaysia"
    },
    "malaysia_movies": {
        "url": "https://www.netflix.com/tudum/top10/malaysia",
        "type": "movie",
        "region": "malaysia"
    }
}

def fetch_page(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Encoding": "gzip, deflate"
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""

def scrape_all() -> dict[str, list[dict]]:
    results = {}
    
    for key, config in SCRAPE_TARGETS.items():
        logger.info(f"Scraping {key} from {config['url']}")
        html = fetch_page(config['url'])
        if html:
            items = parse_tudum_page(html, config['region'], config['type'])
            results[key] = [item.dict() for item in items]
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

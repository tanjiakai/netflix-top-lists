import requests
import logging
from typing import Optional
from urllib.parse import quote
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

CINEMETA_URL = "https://v3-cinemeta.strem.io/catalog/{type}/search={query}.json"

def clean_title(title: str) -> str:
    # Remove "Season X", "Limited Series", "Volume X"
    title = re.sub(r":? Season \d+", "", title, flags=re.IGNORECASE)
    title = re.sub(r":? Limited Series", "", title, flags=re.IGNORECASE)
    title = re.sub(r":? Volume \d+", "", title, flags=re.IGNORECASE)
    return title.strip()

def resolve_to_imdb(title: str, media_type: str) -> Optional[str]:
    """
    Resolves a title to an IMDB ID using Cinemeta.
    """
    try:
        cleaned_title = clean_title(title)
        # If cleaning didn't change much, or if we want to be safe, try both?
        # Let's just use cleaned title.
        
        encoded_query = quote(cleaned_title)
        url = CINEMETA_URL.format(type=media_type, query=encoded_query)
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        metas = data.get("metas", [])
        if metas:
            # Verify the result matches the query
            # Cinemeta returns popular results if no match found, so we MUST verify
            first_result = metas[0]
            result_name = first_result["name"]
            
            # Simple fuzzy match
            ratio = SequenceMatcher(None, cleaned_title.lower(), result_name.lower()).ratio()
            if ratio > 0.8 or cleaned_title.lower() in result_name.lower() or result_name.lower() in cleaned_title.lower():
                 return first_result["imdb_id"]
            else:
                logger.warning(f"Rejecting mismatch: '{cleaned_title}' vs '{result_name}' (ratio={ratio:.2f})")
                
    except Exception as e:
        logger.warning(f"Failed to resolve '{title}': {e}")
        
    return None

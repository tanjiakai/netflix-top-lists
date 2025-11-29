from typing import List, Dict, Any

MANIFEST = {
    "id": "org.stremio.netflix_top_lists",
    "version": "1.0.0",
    "name": "Netflix Top Lists",
    "description": "Daily updated Top 10 TV Shows and Movies from Netflix Tudum (Malaysia)",
    "types": ["movie", "series"],
    "catalogs": [
        {
            "type": "series",
            "id": "malaysia_tv",
            "name": "Netflix Top 10 TV (MY)",
            "extra": [{"name": "skip"}]
        },
        {
            "type": "movie",
            "id": "malaysia_movies",
            "name": "Netflix Top 10 Movies (MY)",
            "extra": [{"name": "skip"}]
        }
    ],
    "resources": ["catalog", "meta"],
    "idPrefixes": []
}

from pydantic import BaseModel
from typing import Optional

class ScrapedItem(BaseModel):
    id: str
    title: str
    poster: str
    rank: int
    type: str  # "movie" or "series"
    region: str
    url: str
    description: Optional[str] = None
    imdb_id: Optional[str] = None  # IMDb ID for Stremio integration
    tmdb_poster: Optional[str] = None # TMDB Poster path (e.g. /path.jpg)

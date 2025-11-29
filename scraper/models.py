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

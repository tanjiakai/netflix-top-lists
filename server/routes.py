from fastapi import APIRouter, HTTPException, Path
from .manifest import MANIFEST
from storage.database import JsonStorage

router = APIRouter()
storage = JsonStorage()

@router.get("/manifest.json")
async def get_manifest():
    return MANIFEST

async def get_catalog_response(type: str, id: str, skip: int = 0):
    # Validate catalog ID
    valid_ids = [c["id"] for c in MANIFEST["catalogs"]]
    if id not in valid_ids:
        raise HTTPException(status_code=404, detail="Catalog not found")
        
    # Load data
    data = storage.load()
    items = data.get(id, [])
    
    # Apply pagination
    items = items[skip:]
    
    # Format for Stremio - rank only used for ordering, not display
    metas = []
    for item in items:
        # Use IMDb ID if available, otherwise fall back to custom ID
        meta_id = item.get("imdb_id") or item.get("id", "")
        
        meta = {
            "id": meta_id,
            "type": item.get("type", "movie"),
            "name": item.get("title"),  # No rank prefix
        }
        
        # Poster Logic:
        # 1. Use TMDB poster if available (High quality, standard)
        # 2. Fallback to scraped poster (Netflix) if no TMDB poster
        if item.get("tmdb_poster"):
            meta["poster"] = f"https://image.tmdb.org/t/p/w500{item.get('tmdb_poster')}"
        elif item.get("poster"):
            meta["poster"] = item.get("poster")
        
        metas.append(meta)
        
    return {"metas": metas}

@router.get("/catalog/{type}/{id}.json")
async def get_catalog(
    type: str = Path(..., description="The type of catalog (movie or series)"),
    id: str = Path(..., description="The catalog ID (e.g., malaysia_tv)")
):
    return await get_catalog_response(type, id)

@router.get("/catalog/{type}/{id}/{extra}.json")
async def get_catalog_extra(
    type: str = Path(..., description="The type of catalog (movie or series)"),
    id: str = Path(..., description="The catalog ID (e.g., malaysia_tv)"),
    extra: str = Path(..., description="Extra parameters like skip=10")
):
    skip = 0
    if extra:
        params = extra.split('&')
        for param in params:
            if param.startswith('skip='):
                try:
                    skip = int(param.split('=')[1])
                except ValueError:
                    pass
    
    return await get_catalog_response(type, id, skip)

@router.get("/meta/{type}/{id}.json")
async def get_meta(
    type: str = Path(..., description="The type (movie or series)"),
    id: str = Path(..., description="The IMDb ID or custom ID")
):
    # Load data
    data = storage.load()
    
    # Search through all catalogs for the item
    for catalog_items in data.values():
        for item in catalog_items:
            # Match by IMDb ID or custom ID
            if item.get("imdb_id") == id or item.get("id") == id:
                meta_id = item.get("imdb_id") or item.get("id", "")
                meta_obj = {
                    "id": meta_id,
                    "type": item.get("type", "movie"),
                    "name": item.get("title"),  # No rank
                }
                
                # Poster Logic:
                # 1. Use TMDB poster if available
                # 2. Fallback to scraped poster
                poster_url = None
                if item.get("tmdb_poster"):
                    poster_url = f"https://image.tmdb.org/t/p/w500{item.get('tmdb_poster')}"
                elif item.get("poster"):
                    poster_url = item.get("poster")
                    
                if poster_url:
                    meta_obj["poster"] = poster_url
                    meta_obj["background"] = poster_url
                
                return {"meta": meta_obj}
    
    raise HTTPException(status_code=404, detail="Meta not found")

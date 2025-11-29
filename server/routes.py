from fastapi import APIRouter, HTTPException, Path
from .manifest import MANIFEST
from storage.database import JsonStorage

router = APIRouter()
storage = JsonStorage()

@router.get("/manifest.json")
async def get_manifest():
    return MANIFEST

@router.get("/catalog/{type}/{id}.json")
async def get_catalog(
    type: str = Path(..., description="The type of catalog (movie or series)"),
    id: str = Path(..., description="The catalog ID (e.g., malaysia_tv)")
):
    # Validate catalog ID
    valid_ids = [c["id"] for c in MANIFEST["catalogs"]]
    if id not in valid_ids:
        raise HTTPException(status_code=404, detail="Catalog not found")
        
    # Load data
    data = storage.load()
    items = data.get(id, [])
    
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
        
        # Don't include poster - let Stremio fetch from cinemeta using IMDb ID
        
        metas.append(meta)
        
    return {"metas": metas}

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
                
                # Don't include poster - let Stremio fetch from cinemeta using IMDb ID
                
                return {"meta": meta_obj}
    
    raise HTTPException(status_code=404, detail="Meta not found")

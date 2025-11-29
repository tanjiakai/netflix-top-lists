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
    
    # Format for Stremio
    metas = []
    for item in items:
        metas.append({
            "id": item.get("id", ""),
            "type": item.get("type", "movie"),
            "name": f"#{item.get('rank')} {item.get('title')}",
            "poster": item.get("poster"),
            "description": item.get("description") or f"Ranked #{item.get('rank')} on Netflix Top 10",
        })
        
    return {"metas": metas}

@router.get("/meta/{type}/{id}.json")
async def get_meta(
    type: str = Path(..., description="The type of meta (movie or series)"),
    id: str = Path(..., description="The meta ID")
):
    # Load data
    data = storage.load()
    
    # Search for the item in all catalogs
    found_item = None
    for catalog_id, items in data.items():
        for item in items:
            if item.get("id") == id:
                found_item = item
                break
        if found_item:
            break
            
    if not found_item:
        raise HTTPException(status_code=404, detail="Meta not found")
        
    meta = {
        "id": found_item.get("id"),
        "type": found_item.get("type"),
        "name": found_item.get("title"),
        "poster": found_item.get("poster"),
        "description": found_item.get("description"),
        "background": found_item.get("poster"), # Use poster as background for now
        "genres": ["Netflix", "Top 10"],
        "releaseInfo": f"Rank #{found_item.get('rank')}"
    }
        
    return {"meta": meta}

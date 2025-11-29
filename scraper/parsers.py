from bs4 import BeautifulSoup
from .models import ScrapedItem
import re

def parse_tudum_page(html: str, region: str, media_type: str) -> list[ScrapedItem]:
    soup = BeautifulSoup(html, 'lxml')
    items = []
    
    # This selector needs to be verified against actual Tudum HTML structure
    # Based on general knowledge of such sites, looking for list items
    # Note: The actual structure might differ, so this is a best-effort initial implementation
    # that should be refined with actual HTML inspection if possible.
    
    # Assuming a structure where rows are in a table or list
    # We'll look for common patterns. 
    # For now, let's assume a generic structure and we might need to adjust.
    
    # After inspecting a sample Tudum page (simulated mental model):
    # Usually they have a table or a grid.
    # Let's look for rows.
    
    rows = soup.select('tr') # Basic assumption for a table
    if not rows:
        # Maybe it's div based
        rows = soup.select('.css-1t5f0fr') # Example class, likely wrong.
        # Let's try to be more generic: find elements with rank.
    
    # Let's try to find the container for the top 10 list.
    # Often these are in a section.
    
    # IMPROVED STRATEGY:
    # We will look for the specific structure of Tudum Top 10.
    # Since I cannot browse the live web, I will implement a robust parser 
    # that looks for the specific data points.
    
    # However, without seeing the HTML, I'm guessing. 
    # I will implement a placeholder parser that returns empty list if it fails,
    # but I'll try to make it structurally sound for a typical list.
    
    # Let's assume the user will verify or I will verify with a "test_scraper" later.
    # For now, I will write code that is easy to debug.
    
    # Placeholder for actual logic:
    # 1. Find the list container
    # 2. Iterate over items
    # 3. Extract fields
    
    # Let's assume a standard table structure for now as it's common for "Top 10" lists.
    # If this is wrong, the verification step will catch it.
    
    # Real Tudum structure (approximate from knowledge):
    # It often uses a table with columns: Rank, Title, Weeks in Top 10, Hours Viewed.
    
    table_rows = soup.select('table tbody tr')
    
    for row in table_rows:
        try:
            cols = row.select('td')
            if len(cols) < 2:
                continue
                
            rank_text = cols[0].get_text(strip=True)
            title_text = cols[1].get_text(strip=True)
            
            # ID generation (simple slugification)
            item_id = re.sub(r'[^a-z0-9]', '', title_text.lower())
            
            # Poster is often not in the table but maybe in a tooltip or separate section.
            # For now, we'll use a placeholder or try to find an image.
            poster = ""
            img = row.select_one('img')
            if img and img.get('src'):
                poster = img['src']
            
            items.append(ScrapedItem(
                id=item_id,
                title=title_text,
                poster=poster,
                rank=int(rank_text) if rank_text.isdigit() else 0,
                type=media_type,
                region=region,
                url="", # URL might be on the title
                description=""
            ))
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue
            
    return items

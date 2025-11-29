from bs4 import BeautifulSoup
from .models import ScrapedItem
import re

def parse_tudum_page(html: str, region: str, media_type: str) -> list[ScrapedItem]:
    soup = BeautifulSoup(html, 'lxml')
    items = []
    
    cards = soup.find_all("div", attrs={"data-uia": "top10-card"})
    
    for card in cards:
        try:
            # Title is in the alt of the first image (logo)
            img = card.find("img")
            if not img or not img.get("alt"):
                continue
            
            title = img.get("alt")
            
            # Rank
            # Look for text like "#1 in Shows"
            rank = 0
            rank_container = card.find(string=re.compile(r"#\d+ in"))
            if rank_container:
                match = re.search(r"#(\d+)", rank_container)
                if match:
                    rank = int(match.group(1))
            
            # Poster (Background Image)
            poster = ""
            style = card.get("style", "")
            # Extract url(...)
            match = re.search(r"url\((.*?)\)", style)
            if match:
                poster = match.group(1)
            
            # ID generation
            item_id = re.sub(r'[^a-z0-9]', '', title.lower())
            
            items.append(ScrapedItem(
                id=item_id,
                title=title,
                poster=poster,
                rank=rank,
                type=media_type,
                region=region,
                url="", 
                description=f"Ranked #{rank} in {region} {media_type}"
            ))
        except Exception as e:
            print(f"Error parsing card: {e}")
            continue
            
    return items

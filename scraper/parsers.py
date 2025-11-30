from bs4 import BeautifulSoup
from .models import ScrapedItem
import re

def parse_flixpatrol_page(html: str, region: str, media_type: str) -> list[ScrapedItem]:
    soup = BeautifulSoup(html, 'lxml')
    items = []
    
    # Determine which section heading to find based on media_type
    if media_type == "movie":
        section_heading = "TOP 10 Movies"
    else:  # series
        section_heading = "TOP 10 TV Shows"
    
    # Find the h3 heading with the section name
    heading = soup.find('h3', string=section_heading)
    if not heading:
        # Try case-insensitive regex search
        heading = soup.find('h3', string=re.compile(section_heading, re.IGNORECASE))
    
    if not heading:
        return items
    
    # Find the parent card div and locate the table within it
    card_div = heading.find_parent('div', class_='card')
    if not card_div:
        return items
    
    # Find the table within the card
    table = card_div.find('table')
    if not table:
        return items
    
    # Find all table rows
    rows = table.find('tbody').find_all('tr', class_='table-group')
    
    # Parse each row
    for idx, row in enumerate(rows[:10], start=1):
        try:
            # Find the link within the row
            link = row.find('a', href=re.compile(r'^/title/'))
            if not link:
                continue
            
            title = link.get_text (strip=True)
            if not title:
                continue
            
            # Generate ID from title
            item_id = re.sub(r'[^a-z0-9]', '', title.lower())
            
            # FlixPatrol doesn't provide posters in the list, leave empty
            poster = ""
            
            items.append(ScrapedItem(
                id=item_id,
                title=title,
                poster=poster,
                rank=idx,
                type=media_type,
                region=region,
                url=f"https://flixpatrol.com{link.get('href', '')}",
                description=f"Ranked #{idx} in {region} {media_type}"
            ))
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue
    
    return items

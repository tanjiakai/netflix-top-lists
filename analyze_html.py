from bs4 import BeautifulSoup

with open("debug.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

# Find the first card
card = soup.find("div", attrs={"data-uia": "top10-card"})
if card:
    print(f"Card found: {card.attrs}")
    print("--- Images ---")
    for img in card.find_all("img"):
        print(f"Img src: {img.get('src')}")
        print(f"Img alt: {img.get('alt')}")
        print(f"Img title: {img.get('title')}")

print("--- Script Tags ---")
for script in soup.find_all("script"):
    if script.string and "top10" in script.string:
        print(f"Found 'top10' in script (len={len(script.string)})")
        # Print a snippet
        print(script.string[:200])

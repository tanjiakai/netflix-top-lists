# Netflix Top Lists Stremio Add-on

A Stremio add-on that scrapes Netflix Tudum Top 10 lists (Malaysia TV & Movies) daily and serves them via the Stremio Add-on Protocol.

## Features

- **Daily Scraping**: Automatically fetches the latest Top 10 lists from Netflix Tudum.
- **Stremio Protocol**: Fully compliant with the Stremio Add-on Protocol.
- **Extensible**: Designed to easily add more regions and categories.
- **JSON Storage**: Simple, file-based storage for easy deployment and maintenance.

## Project Structure

- `scraper/`: Contains the logic for fetching and parsing Tudum pages.
- `storage/`: Handles data persistence (currently JSON file).
- `server/`: FastAPI application serving the add-on endpoints.
- `workflows/`: GitHub Actions for automation.
- `tests/`: Unit tests.

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the scraper (to populate catalog):
   ```bash
   python -m scraper.scraper
   ```

3. Run the server:
   ```bash
   uvicorn server.app:app --reload
   ```

## Deployment

This project is ready to be deployed on Render.com or any platform supporting Python web apps.

# Netflix Top Lists Stremio Add-on

A Stremio add-on that scrapes Netflix Tudum Top 10 lists (Malaysia TV & Movies) daily and serves them via the Stremio Add-on Protocol. **Features TMDB integration** to provide IMDb IDs, enabling other Stremio add-ons to provide streams.

## Features

- **Daily Scraping**: Automatically fetches the latest Top 10 lists from Netflix Tudum.
- **TMDB Integration**: Fetches IMDb IDs for all titles, enabling stream discovery from other add-ons.
- **Stremio Protocol**: Fully compliant with the Stremio Add-on Protocol.
- **Extensible**: Designed to easily add more regions and categories.
- **JSON Storage**: Simple, file-based storage for easy deployment and maintenance.

## Setup

### 1. Get TMDB API Key (Required)

To enable IMDb ID lookup and stream integration:

1. Create a free account at [TMDB](https://www.themoviedb.org/)
2. Get your API key from [Settings > API](https://www.themoviedb.org/settings/api)
3. Copy `.env.example` to `.env` and add your key:
   ```bash
   cp .env.example .env
   # Edit .env and add: TMDB_API_KEY=your_api_key_here
   ```

### 2. Run Locally

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

### Render.com

1. Set environment variable `TMDB_API_KEY` in Render dashboard
2. The app will automatically deploy from GitHub


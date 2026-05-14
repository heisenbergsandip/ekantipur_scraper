# Ekantipur News Scraper

A Playwright-based web scraper for extracting entertainment news and cartoons from [ekantipur.com](https://ekantipur.com).

## Features

- **Entertainment News Extraction**: Scrapes top 5 articles from the entertainment section with title, image URL, category, and author
- **Cartoon of the Day**: Extracts the latest cartoon with title, image URL, and cartoonist name
- **Lazy Loading Support**: Handles dynamically loaded images by detecting both `data-src` and `src` attributes
- **Robust Error Handling**: Individual card failures don't crash the entire extraction process
- **UTF-8 Encoding**: Properly preserves Nepali Devanagari text in output JSON
- **Fallback Strategy**: Uses homepage cartoon slider if dedicated page unavailable

## Requirements

- Python 3.10+
- Playwright browser automation library

## Installation

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
mkdir ekantipur-scraper && cd ekantipur-scraper
uv init

# Install dependencies
uv add playwright
uv run playwright install chromium
```

## Usage

```bash
# Run the scraper
uv run python scraper.py

# The script will:
# 1. Navigate to ekantipur.com/cartoon and extract the latest cartoon
# 2. Navigate to ekantipur.com/entertainment and extract top 5 articles
# 3. Write results to output.json with UTF-8 encoding
```

## Output Format

The scraper generates `output.json` with the following structure:

```json
{
  "entertainment_news": [
    {
      "title": "Article headline",
      "image_url": "https://...",
      "category": "मनोरञ्जन",
      "author": "Author Name or null"
    }
  ],
  "cartoon_of_the_day": {
    "title": "Cartoon title",
    "image_url": "https://...",
    "author": "Cartoonist Name or null"
  }
}
```

## Implementation Details

### Main Functions

- `scrape_entertainment_news(page)`: Extracts top 5 entertainment articles
- `scrape_cartoon_of_day(page)`: Extracts latest cartoon with fallback to homepage
- `_get_image_url(card)`: Helper to handle lazy-loaded images
- `_extract_category_from_url(href)`: Helper to map URLs to Nepali category names
- `main()`: Orchestrates the full scraping workflow

### Key Design Decisions

1. **Lazy Loading**: Scrolls to trigger image loading and waits 1.5 seconds before extraction
2. **Fallback Mechanism**: Falls back to homepage carousel if dedicated cartoon page unavailable
3. **Error Resilience**: Uses try/except per card to allow partial results
4. **Selector Strategy**: Prefers semantic HTML selectors and Playwright locators over XPath
5. **Author Handling**: Returns `null` (not empty string) when author not found, per specification

## Notes

- The script uses `headless=False` mode for debugging/visibility. Change to `headless=True` in production for speed.
- Nepali text is preserved with `ensure_ascii=False` in JSON output
- The scraper includes realistic User-Agent headers to minimize bot detection

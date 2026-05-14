"""
Ekantipur News Scraper - Audio Bee Practical Test

Scrapes entertainment news and cartoon of the day from https://ekantipur.com
Outputs structured JSON data with proper UTF-8 encoding for Nepali text.

Tasks:
1. Extract top 5 entertainment articles with: title, image_url, category, author
2. Extract "Cartoon of the Day" with: title, image_url, author

Implementation:
- Uses Playwright for browser automation
- Handles lazy-loaded images (data-src fallback to src)
- Robust error handling per card (skip failures, continue extraction)
- Proper Nepali text encoding (ensure_ascii=False)
"""

import json
from playwright.sync_api import sync_playwright, Page, Locator


def _get_image_url(card: Locator) -> str | None:
    """
    Extract image URL from card element.
    Handles both lazy-loaded images (data-src) and already-loaded images (src).
    Normalizes relative URLs to absolute URLs.
    """
    img = card.locator("img").first
    
    if not img.count():
        return None
    
    # Try data-src first (lazy images), then src (already loaded)
    url = img.get_attribute("data-src") or img.get_attribute("src")
    
    if not url or not url.strip():
        return None
    
    url = url.strip()
    
    # Normalize protocol-relative URLs (//assets...) to https://
    if url.startswith("//"):
        url = "https:" + url
    # Normalize root-relative URLs (/uploads...) to full domain
    elif url.startswith("/"):
        url = "https://ekantipur.com" + url
    
    return url


def _parse_title_and_author(text: str | None) -> tuple[str | None, str | None]:
    """
    Parse title and author from "Title - Author" format.
    Handles various dash types (-, –, —) and missing authors.
    Returns (title, author) tuple. Either can be None if not found.
    """
    if not text or not text.strip():
        return None, None
    
    text = text.strip()
    
    # Try multiple dash types: regular hyphen, en-dash, em-dash
    for dash in [" - ", " – ", " — "]:
        if dash in text:
            parts = text.rsplit(dash, 1)  # Split from right to handle titles with dashes
            title = parts[0].strip()
            author = parts[1].strip() if len(parts) > 1 else None
            
            # Return title if it exists, even if author is empty
            if title:
                return (title, author if author else None)
    
    # No separator found, treat entire text as title
    return (text, None)


def _extract_category_from_url(href: str | None) -> str:
    """
    Extract category name from article URL.
    Returns appropriate Nepali category label based on URL pattern.
    """
    if not href:
        return "मनोरञ्जन"
    
    if "/entertainment/" in href:
        return "मनोरञ्जन"
    elif "/bollywood/" in href:
        return "बलिउड"
    
    return "मनोरञ्जन"


def scrape_entertainment_news(page: Page) -> list[dict]:
    """
    Extract top 5 entertainment articles from ekantipur.com/entertainment.
    
    For each article card, extracts:
    - title: article headline
    - image_url: article thumbnail URL (handles lazy loading)
    - category: category label derived from URL
    - author: author name(s), null if not found
    
    Handles missing/malformed elements gracefully.
    Returns list of up to 5 article dictionaries.
    """
    page.goto("https://ekantipur.com/entertainment", wait_until="domcontentloaded")
    page.wait_for_selector("div.category-inner-wrapper", timeout=15000)
    
    # Scroll to trigger lazy image loading
    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    page.wait_for_timeout(1500)
    
    cards = page.locator("div.category-inner-wrapper").all()
    results = []
    
    for idx, card in enumerate(cards[:5], 1):
        try:
            # Extract title
            title_el = card.locator("div.category-description h2 a").first
            title = title_el.inner_text().strip() if title_el.count() else None
            
            if not title:
                continue
            
            # Extract author(s)
            author_links = card.locator("div.author-name p a").all()
            if author_links:
                authors = [a.inner_text().strip() for a in author_links if a.inner_text().strip()]
                author = ", ".join(authors) if authors else None
            else:
                author = None
            
            # Extract image URL
            image_url = _get_image_url(card)
            
            # Extract category from URL
            href = title_el.get_attribute("href") if title_el.count() else None
            category = _extract_category_from_url(href)
            
            results.append({
                "title": title,
                "image_url": image_url,
                "category": category,
                "author": author
            })
            
        except Exception as e:
            continue
    
    return results


def scrape_cartoon_of_day(page: Page) -> dict[str, str | None]:
    """
    Extract the latest "Cartoon of the Day" from ekantipur.com/cartoon.
    
    Extracts:
    - title: cartoon caption/title
    - image_url: cartoon image URL (handles lazy loading)
    - author: cartoonist name
    
    Handles both structured (h2 a) and flat text (p with "Title - Author") formats.
    Falls back to homepage cartoon slider if dedicated page unavailable.
    Returns dictionary with title, image_url, author (any can be None).
    """
    page.goto("https://ekantipur.com/cartoon", wait_until="domcontentloaded")
    
    try:
        page.wait_for_selector("div.cartoon-wrapper", timeout=10000)
    except Exception:
        return _scrape_cartoon_fallback(page)
    
    first_card = page.locator("div.cartoon-wrapper").first
    
    if not first_card.count():
        return _scrape_cartoon_fallback(page)
    
    # Extract image URL
    image_url = _get_image_url(first_card)
    
    # Extract title and author from description paragraph
    # Handles format: "Title - Author"
    desc_p = first_card.locator("div.cartoon-description p").first
    if desc_p.count():
        desc_text = desc_p.inner_text().strip()
        title, author = _parse_title_and_author(desc_text)
    else:
        title, author = None, None
    
    return {
        "title": title,
        "image_url": image_url,
        "author": author
    }


def _scrape_cartoon_fallback(page: Page) -> dict[str, str | None]:
    """
    Fallback: scrape cartoon from homepage slider if dedicated /cartoon page fails.
    
    Extracts title and author from cartoon description text ("Title - Author" format).
    Returns dictionary with title, image_url, author.
    """
    page.goto("https://ekantipur.com", wait_until="domcontentloaded")
    
    try:
        page.wait_for_selector("div.swiper.cartoon-slider", timeout=8000)
    except Exception:
        return {"title": None, "image_url": None, "author": None}
    
    # Get first slide
    first_slide = page.locator("div.swiper.cartoon-slider .swiper-slide").first
    img = first_slide.locator("img").first
    
    if not img.count():
        return {"title": None, "image_url": None, "author": None}
    
    image_url = _get_image_url(first_slide)
    
    #  Extract title and author from description paragraph
    desc_p = first_slide.locator("div.cartoon-description p").first
    if desc_p.count():
        desc_text = desc_p.inner_text().strip()
        title, author = _parse_title_and_author(desc_text)
    else:
        # Fallback to alt text if no description paragraph
        title = img.get_attribute("alt")
        if title:
            title = title.strip()
        author = None
    
    return {
        "title": title,
        "image_url": image_url,
        "author": author
    }


def main() -> None:
    """
    Main entry point: orchestrates the full scraping workflow.
    
    Execution:
    1. Launch browser (headless=False for debugging)
    2. Scrape cartoon of the day
    3. Scrape entertainment news
    4. Combine results into output dictionary
    5. Write to output.json with UTF-8 encoding (preserves Nepali text)
    6. Close browser
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            # Extract cartoon
            cartoon = scrape_cartoon_of_day(page)
            
            # Extract entertainment news
            entertainment_news = scrape_entertainment_news(page)
            
            # Build output structure
            output = {
                "entertainment_news": entertainment_news,
                "cartoon_of_the_day": cartoon
            }
            
            # Write JSON with UTF-8 encoding for Nepali text
            with open("output.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print("\nScraping completed successfully!")
            print(f"  - Entertainment articles: {len(entertainment_news)}")
            print(f"  - Cartoon: {cartoon.get('title', 'N/A')[:40]}")
            print("  - Output saved to output.json")
            
        except Exception as e:
            print(f"Error during scraping: {type(e).__name__}: {e}")
            raise
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
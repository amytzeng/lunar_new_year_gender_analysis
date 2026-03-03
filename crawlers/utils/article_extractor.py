"""
Article content extraction utility module
Provides functions to extract article content from various news websites
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Optional
import time

# User-Agent header to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def extract_actual_url_from_google_news(google_news_url: str) -> str:
    """
    Extract the actual news website URL from a Google News redirect link
    
    Args:
        google_news_url: The Google News URL that redirects to the actual article
        
    Returns:
        The actual news website URL
    """
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # Google News RSS articles URLs need to be accessed to get the actual link
        # The actual URL is usually in the page's HTML or redirect chain
        r = session.get(google_news_url, timeout=15, allow_redirects=True)
        
        # Check if we got redirected to the actual news site
        final_url = r.url
        if "news.google.com" not in final_url:
            return final_url
        
        # If still on Google News, parse the HTML to find the actual article link
        try:
            soup = BeautifulSoup(r.text, "lxml")
            
            # Method 1: Look for canonical link
            canonical = soup.find("link", rel="canonical")
            if canonical and canonical.get("href"):
                href = canonical.get("href")
                if href and "news.google.com" not in href:
                    return href
            
            # Method 2: Look for og:url meta tag
            og_url = soup.find("meta", property="og:url")
            if og_url and og_url.get("content"):
                content = og_url.get("content")
                if content and "news.google.com" not in content:
                    return content
            
            # Method 3: Look for the main article link in the page
            # Google News pages often have a prominent link to the actual article
            # Look for links with specific patterns
            article_links = soup.find_all("a", href=True)
            for link in article_links:
                href = link.get("href", "")
                if not href:
                    continue
                
                # Skip Google domains
                if "google.com" in href or "gstatic.com" in href:
                    continue
                
                # Look for full URLs that point to news sites
                if href.startswith("http"):
                    # Check if it's a known news domain
                    news_domains = ["cnn.com", "bbc.com", "reuters.com", "apnews.com", 
                                   "theguardian.com", "washingtonpost.com", "nytimes.com",
                                   "nbcnews.com", "cbsnews.com", "foxnews.com", "abcnews.go.com"]
                    if any(domain in href for domain in news_domains):
                        return href
                
                # Also check for relative URLs that might be expanded
                if href.startswith("/") and len(href) > 10:
                    # This might be a relative link, but we need the base URL
                    # Skip for now as we don't know the base
                    pass
            
            # Method 4: Try to extract from JavaScript variables
            # Some Google News pages embed the URL in JavaScript
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string:
                    script_text = script.string
                    # Look for URL patterns in JavaScript
                    import re
                    # Look for URLs in quotes
                    url_pattern = r'["\'](https?://[^"\']+)["\']'
                    matches = re.findall(url_pattern, script_text)
                    for match in matches:
                        if "news.google.com" not in match:
                            news_domains = ["cnn.com", "bbc.com", "reuters.com", "apnews.com"]
                            if any(domain in match for domain in news_domains):
                                return match
            
            # Method 5: Look for data attributes
            for element in soup.find_all(attrs={"data-url": True}):
                data_url = element.get("data-url")
                if data_url and "news.google.com" not in data_url:
                    if data_url.startswith("http"):
                        return data_url
            
        except Exception:
            pass
        
        # If all methods fail, return the final URL (might still be Google News)
        return final_url
    except Exception:
        # If extraction fails, return original URL
        return google_news_url


def fetch_article_content(url: str, selectors: List[str], max_retries: int = 3) -> str:
    """
    Fetch and extract article content from a URL using multiple CSS selectors
    
    This function tries each selector in order until it finds content.
    If all selectors fail, it falls back to extracting all paragraph tags.
    
    Args:
        url: The article URL to fetch
        selectors: List of CSS selectors to try in order
        max_retries: Maximum number of retry attempts for fetching the page
        
    Returns:
        Extracted article content as a string, or an error message if extraction fails
    """
    # Handle Google News redirect links
    actual_url = url
    if "news.google.com" in url:
        actual_url = extract_actual_url_from_google_news(url)
    
    # Fetch the page with retries
    r = None
    for attempt in range(max_retries):
        try:
            r = requests.get(actual_url, timeout=15, allow_redirects=True, headers=HEADERS)
            r.raise_for_status()
            break
        except Exception as e:
            if attempt == max_retries - 1:
                return f"[Error fetching page: {e}]"
            time.sleep(1)  # Wait before retry
    
    if r is None:
        return "[Error fetching page: Request failed]"
    
    # Parse HTML
    try:
        soup = BeautifulSoup(r.text, "lxml")
    except Exception as e:
        return f"[Error parsing HTML: {e}]"
    
    # Try each selector in order
    paragraphs = []
    for selector in selectors:
        try:
            container = soup.select_one(selector)
            if container:
                # Extract paragraphs from the container
                paragraph_tags = container.find_all("p", recursive=True)
                paragraphs = [
                    p.get_text(" ", strip=True) 
                    for p in paragraph_tags 
                    if p.get_text(" ", strip=True) and len(p.get_text(" ", strip=True)) > 20
                ]
                if paragraphs:
                    break
        except Exception:
            continue
    
    # Fallback 1: try to find all paragraphs if selectors failed
    if not paragraphs:
        try:
            all_paragraphs = soup.find_all("p")
            paragraphs = [
                p.get_text(" ", strip=True) 
                for p in all_paragraphs 
                if p.get_text(" ", strip=True) and len(p.get_text(" ", strip=True)) > 20
            ]
        except Exception:
            pass
    
    # Fallback 2: try article, main, or content-like elements
    if not paragraphs:
        try:
            for tag_name in ["article", "main", "div[role='article']", "div.article", "div.content"]:
                elements = soup.select(tag_name)
                for elem in elements:
                    text = elem.get_text(" ", strip=True)
                    if text and len(text) > 200:  # Longer text likely to be article content
                        # Try to extract paragraphs from this element
                        para_tags = elem.find_all("p")
                        if para_tags:
                            paragraphs = [
                                p.get_text(" ", strip=True) 
                                for p in para_tags 
                                if p.get_text(" ", strip=True) and len(p.get_text(" ", strip=True)) > 20
                            ]
                            if paragraphs:
                                break
                if paragraphs:
                    break
        except Exception:
            pass
    
    # Fallback 3: try div elements with substantial text content
    if not paragraphs:
        try:
            div_elements = soup.find_all("div", recursive=True)
            for div in div_elements:
                text = div.get_text(" ", strip=True)
                # Check if this div has substantial text and contains multiple sentences
                if text and len(text) > 200 and text.count('.') > 3:
                    paragraphs = [text]
                    break
        except Exception:
            pass
    
    return "\n".join(paragraphs) if paragraphs else "[No article text found]"


def extract_title_from_html(url: str, soup: Optional[BeautifulSoup] = None) -> str:
    """
    Extract article title from HTML
    
    Args:
        url: The article URL (for fallback)
        soup: BeautifulSoup object (optional, will fetch if not provided)
        
    Returns:
        Article title or a default title
    """
    if soup is None:
        try:
            r = requests.get(url, timeout=15, allow_redirects=True)
            soup = BeautifulSoup(r.text, "lxml")
        except:
            return "Article"
    
    # Try various title selectors
    title_selectors = [
        "h1",
        "title",
        "meta[property='og:title']",
        "meta[name='twitter:title']",
    ]
    
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element:
            if selector.startswith("meta"):
                title = element.get("content", "")
            else:
                title = element.get_text(strip=True)
            if title:
                return title
    
    return "Article"

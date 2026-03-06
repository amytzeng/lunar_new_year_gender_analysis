"""
Google News URL decoder utility module
Provides functions to decode Google News encoded URLs to actual article URLs
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import time
import re
import random

# Try to import googlenewsdecoder, fallback to requests if not available
try:
    from googlenewsdecoder import new_decoderv1
    HAS_DECODER = True
except ImportError:
    HAS_DECODER = False

# User-Agent headers to avoid being blocked (rotate between different ones)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
]

# Default headers
HEADERS = {
    'User-Agent': USER_AGENTS[0],
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def normalize_google_news_url(url: str) -> str:
    """
    Normalize Google News URL format for decoding
    
    Converts /rss/articles/ to /articles/ format which is required
    by some decoders.
    
    Args:
        url: Google News URL
        
    Returns:
        Normalized URL
    """
    # Convert /rss/articles/ to /articles/ format
    if "/rss/articles/" in url:
        url = url.replace("/rss/articles/", "/articles/")
    return url


def decode_with_googlenewsdecoder(google_news_url: str) -> Optional[str]:
    """
    Decode Google News URL using googlenewsdecoder package
    
    This method uses algorithm-based decoding without making network requests,
    making it fast and avoiding IP blocking.
    
    Args:
        google_news_url: The Google News encoded URL
        
    Returns:
        Decoded URL if successful, None otherwise
    """
    if not HAS_DECODER:
        return None
    
    try:
        # Normalize URL format (convert /rss/articles/ to /articles/)
        normalized_url = normalize_google_news_url(google_news_url)
        
        # Try with normalized URL first
        result = new_decoderv1(normalized_url)
        if result.get("status"):
            decoded_url = result.get("decoded_url")
            if decoded_url and decoded_url != normalized_url and decoded_url != google_news_url:
                return decoded_url
        
        # If normalized URL didn't work, try original URL
        if normalized_url != google_news_url:
            result = new_decoderv1(google_news_url)
            if result.get("status"):
                decoded_url = result.get("decoded_url")
                if decoded_url and decoded_url != google_news_url:
                    return decoded_url
    except Exception:
        pass
    
    return None


def decode_with_requests(google_news_url: str, max_retries: int = 3) -> Optional[str]:
    """
    Decode Google News URL by following redirects using requests
    
    This method makes network requests to follow redirects and extract
    the actual article URL. It's slower than googlenewsdecoder and may
    trigger rate limiting, but serves as a fallback method.
    
    Args:
        google_news_url: The Google News encoded URL
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decoded URL if successful, None otherwise
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Normalize URL format
    normalized_url = normalize_google_news_url(google_news_url)
    
    for attempt in range(max_retries):
        try:
            # Try normalized URL first
            url_to_try = normalized_url if normalized_url != google_news_url else google_news_url
            
            # Follow redirects to get the final URL
            r = session.get(url_to_try, timeout=15, allow_redirects=True)
            
            # Check if we got redirected to the actual news site
            final_url = r.url
            if "news.google.com" not in final_url and "google.com" not in final_url:
                return final_url
            
            # If still on Google News, try to parse HTML to find the actual link
            try:
                soup = BeautifulSoup(r.text, "lxml")
                
                # Method 1: Look for canonical link
                canonical = soup.find("link", rel="canonical")
                if canonical and canonical.get("href"):
                    href = canonical.get("href")
                    if href and "news.google.com" not in href and "google.com" not in href:
                        return href
                
                # Method 2: Look for og:url meta tag
                og_url = soup.find("meta", property="og:url")
                if og_url and og_url.get("content"):
                    content = og_url.get("content")
                    if content and "news.google.com" not in content and "google.com" not in content:
                        return content
                
                # Method 3: Look for article links in the page
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
                        news_domains = [
                            "cnn.com", "bbc.com", "reuters.com", "apnews.com",
                            "theguardian.com", "washingtonpost.com", "nytimes.com",
                            "nbcnews.com", "cbsnews.com", "foxnews.com", "abcnews.go.com"
                        ]
                        if any(domain in href for domain in news_domains):
                            return href
                
                # Method 4: Look for data attributes or JavaScript variables
                # Some Google News pages embed URLs in data attributes
                for element in soup.find_all(attrs={"data-url": True}):
                    data_url = element.get("data-url")
                    if data_url and data_url.startswith("http") and "news.google.com" not in data_url:
                        return data_url
                
            except Exception:
                pass
            
            # If all parsing methods fail and we're still on Google News, return None
            # (don't return the Google News URL as it's not decoded)
            if "news.google.com" in final_url:
                return None
            
        except Exception as e:
            if attempt < max_retries - 1:
                # Wait before retry
                time.sleep(1)
            else:
                # Last attempt failed
                return None
    
    return None


def decode_with_enhanced_parsing(google_news_url: str, max_retries: int = 3) -> Optional[str]:
    """
    Enhanced decoding method with more thorough HTML parsing
    
    This method uses multiple strategies to extract the actual article URL:
    - More thorough HTML parsing with multiple selectors
    - JavaScript content extraction
    - Multiple User-Agent rotation
    - Longer timeout for slow responses
    - More detailed error handling
    
    Args:
        google_news_url: The Google News encoded URL
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decoded URL if successful, None otherwise
    """
    session = requests.Session()
    
    # Normalize URL format
    normalized_url = normalize_google_news_url(google_news_url)
    
    # List of known news domains to look for
    news_domains = [
        "cnn.com", "bbc.com", "reuters.com", "apnews.com",
        "theguardian.com", "washingtonpost.com", "nytimes.com",
        "nbcnews.com", "cbsnews.com", "foxnews.com", "abcnews.go.com",
        "wsj.com", "bloomberg.com", "usatoday.com", "latimes.com",
        "chicagotribune.com", "bostonglobe.com", "denverpost.com"
    ]
    
    for attempt in range(max_retries):
        try:
            # Rotate User-Agent for each attempt
            headers = HEADERS.copy()
            headers['User-Agent'] = random.choice(USER_AGENTS)
            session.headers.update(headers)
            
            # Try normalized URL first
            url_to_try = normalized_url if normalized_url != google_news_url else google_news_url
            
            # Use longer timeout for enhanced parsing
            r = session.get(url_to_try, timeout=30, allow_redirects=True)
            
            # Check if we got redirected to the actual news site
            final_url = r.url
            if "news.google.com" not in final_url and "google.com" not in final_url:
                # Verify it's a news domain
                if any(domain in final_url for domain in news_domains):
                    return final_url
            
            # Parse HTML with more thorough methods
            try:
                soup = BeautifulSoup(r.text, "lxml")
                
                # Method 1: Look for canonical link
                canonical = soup.find("link", rel="canonical")
                if canonical and canonical.get("href"):
                    href = canonical.get("href")
                    if href and "news.google.com" not in href and "google.com" not in href:
                        if any(domain in href for domain in news_domains):
                            return href
                
                # Method 2: Look for og:url meta tag
                og_url = soup.find("meta", property="og:url")
                if og_url and og_url.get("content"):
                    content = og_url.get("content")
                    if content and "news.google.com" not in content and "google.com" not in content:
                        if any(domain in content for domain in news_domains):
                            return content
                
                # Method 3: Look for all links and find the most likely article link
                article_links = soup.find_all("a", href=True)
                candidate_urls = []
                
                for link in article_links:
                    href = link.get("href", "")
                    if not href:
                        continue
                    
                    # Skip Google domains
                    if "google.com" in href or "gstatic.com" in href or "googleusercontent.com" in href:
                        continue
                    
                    # Look for full URLs
                    if href.startswith("http"):
                        # Check if it's a known news domain
                        for domain in news_domains:
                            if domain in href:
                                # Prioritize links with article-like text
                                link_text = link.get_text(strip=True).lower()
                                priority = 0
                                if any(keyword in link_text for keyword in ["read", "article", "full", "story", "more"]):
                                    priority = 10
                                elif len(link_text) > 20:
                                    priority = 5
                                candidate_urls.append((priority, href))
                                break
                
                # Sort by priority and return the highest priority URL
                if candidate_urls:
                    candidate_urls.sort(key=lambda x: x[0], reverse=True)
                    return candidate_urls[0][1]
                
                # Method 4: Look for data attributes
                for element in soup.find_all(attrs={"data-url": True}):
                    data_url = element.get("data-url")
                    if data_url and data_url.startswith("http") and "news.google.com" not in data_url:
                        if any(domain in data_url for domain in news_domains):
                            return data_url
                
                # Method 5: Extract URLs from JavaScript
                scripts = soup.find_all("script")
                for script in scripts:
                    if script.string:
                        script_text = script.string
                        # Look for URL patterns in JavaScript
                        # Pattern 1: URLs in quotes
                        url_patterns = [
                            r'["\'](https?://[^"\']+)["\']',
                            r'url["\']?\s*[:=]\s*["\'](https?://[^"\']+)["\']',
                            r'href["\']?\s*[:=]\s*["\'](https?://[^"\']+)["\']',
                        ]
                        
                        for pattern in url_patterns:
                            matches = re.findall(pattern, script_text, re.IGNORECASE)
                            for match in matches:
                                if isinstance(match, tuple):
                                    match = match[0] if match else ""
                                if match and "news.google.com" not in match and "google.com" not in match:
                                    for domain in news_domains:
                                        if domain in match:
                                            return match
                
                # Method 6: Look for iframe src attributes (some Google News pages use iframes)
                iframes = soup.find_all("iframe", src=True)
                for iframe in iframes:
                    src = iframe.get("src", "")
                    if src and src.startswith("http") and "news.google.com" not in src:
                        if any(domain in src for domain in news_domains):
                            return src
                
            except Exception:
                pass
            
            # If all parsing methods fail and we're still on Google News, return None
            if "news.google.com" in final_url:
                return None
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait longer before retry
            else:
                return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None
    
    return None


def decode_google_news_url(google_news_url: str, use_fallback: bool = True, use_enhanced: bool = False) -> Dict[str, any]:
    """
    Decode Google News URL to actual article URL
    
    This function tries multiple decoding methods in order:
    1. googlenewsdecoder (fast, no network requests)
    2. enhanced parsing (if enabled, more thorough HTML parsing)
    3. requests redirect following (slower, requires network)
    
    Args:
        google_news_url: The Google News encoded URL
        use_fallback: Whether to use requests method if decoder fails
        use_enhanced: Whether to use enhanced parsing method (slower but more thorough)
        
    Returns:
        Dictionary with keys:
            - success: bool indicating if decoding was successful
            - decoded_url: str with decoded URL (or original if failed)
            - method: str indicating which method was used ("decoder", "requests", or "none")
            - error: str with error message if failed, None otherwise
    """
    # Validate input
    if not google_news_url or not isinstance(google_news_url, str):
        return {
            "success": False,
            "decoded_url": google_news_url,
            "method": "none",
            "error": "Invalid URL input"
        }
    
    # Remove whitespace
    google_news_url = google_news_url.strip()
    
    # Check if it's actually a Google News URL
    if "news.google.com" not in google_news_url:
        return {
            "success": False,
            "decoded_url": google_news_url,
            "method": "none",
            "error": "Not a Google News URL"
        }
    
    # Try method 1: googlenewsdecoder
    decoded_url = decode_with_googlenewsdecoder(google_news_url)
    if decoded_url:
        return {
            "success": True,
            "decoded_url": decoded_url,
            "method": "decoder",
            "error": None
        }
    
    # Try method 2: enhanced parsing (if enabled)
    if use_enhanced:
        decoded_url = decode_with_enhanced_parsing(google_news_url)
        if decoded_url and decoded_url != google_news_url:
            if "news.google.com" not in decoded_url and "google.com" not in decoded_url:
                return {
                    "success": True,
                    "decoded_url": decoded_url,
                    "method": "enhanced",
                    "error": None
                }
            # Check if it contains news domain indicators
            news_indicators = [
                "cnn.com", "bbc.com", "reuters.com", "apnews.com",
                "theguardian.com", "washingtonpost.com", "nytimes.com",
                "nbcnews.com", "cbsnews.com", "foxnews.com", "abcnews.go.com"
            ]
            if any(indicator in decoded_url for indicator in news_indicators):
                return {
                    "success": True,
                    "decoded_url": decoded_url,
                    "method": "enhanced",
                    "error": None
                }
    
    # Try method 3: requests (if fallback enabled)
    if use_fallback:
        decoded_url = decode_with_requests(google_news_url)
        # Check if decoding was successful (URL changed and is not Google News)
        if decoded_url and decoded_url != google_news_url:
            # Additional check: make sure it's not still a Google News URL
            if "news.google.com" not in decoded_url and "google.com" not in decoded_url:
                return {
                    "success": True,
                    "decoded_url": decoded_url,
                    "method": "requests",
                    "error": None
                }
            # If decoded URL still contains google.com, it might be a different Google service
            # Check if it's actually a news article URL (contains common news domains)
            news_indicators = [
                "cnn.com", "bbc.com", "reuters.com", "apnews.com",
                "theguardian.com", "washingtonpost.com", "nytimes.com",
                "nbcnews.com", "cbsnews.com", "foxnews.com", "abcnews.go.com"
            ]
            if any(indicator in decoded_url for indicator in news_indicators):
                return {
                    "success": True,
                    "decoded_url": decoded_url,
                    "method": "requests",
                    "error": None
                }
    
    # Both methods failed - provide more detailed error message
    error_msg = "Failed to decode URL"
    if not HAS_DECODER:
        error_msg += " (googlenewsdecoder not installed)"
    if not use_fallback:
        error_msg += " (fallback disabled)"
    else:
        error_msg += " (both decoder and requests methods failed)"
    
    return {
        "success": False,
        "decoded_url": google_news_url,
        "method": "none",
        "error": error_msg
    }

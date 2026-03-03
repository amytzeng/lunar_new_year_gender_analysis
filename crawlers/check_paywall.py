"""
Check which articles require payment (paywall) to read
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from tqdm import tqdm
from typing import Dict, List, Tuple

# User-Agent header to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Common paywall indicators
PAYWALL_KEYWORDS = [
    "subscribe",
    "subscription",
    "paywall",
    "premium",
    "member exclusive",
    "sign in to continue",
    "sign in to read",
    "create account",
    "free articles remaining",
    "you've reached your article limit",
    "unlock this article",
    "become a member",
    "join now",
    "limited time offer",
]

# Paywall-related CSS classes and IDs
PAYWALL_SELECTORS = [
    "[class*='paywall']",
    "[class*='subscription']",
    "[class*='premium']",
    "[id*='paywall']",
    "[id*='subscription']",
    "[id*='premium']",
    "[data-paywall]",
    "[data-subscription]",
]

# Meta tags that indicate paywall
PAYWALL_META_TAGS = [
    "paywall",
    "subscription",
    "premium",
]


def check_paywall(url: str, timeout: int = 10) -> Tuple[bool, str, int]:
    """
    Check if an article requires payment to read
    
    Args:
        url: Article URL to check
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (has_paywall, reason, content_length)
        - has_paywall: True if paywall detected, False otherwise
        - reason: Reason for paywall detection or "free" if no paywall
        - content_length: Length of page content
    """
    try:
        # Handle Google News redirect URLs
        actual_url = url
        if "news.google.com" in url:
            # Try to follow redirect
            try:
                r = requests.get(url, timeout=timeout, allow_redirects=True, headers=HEADERS)
                actual_url = r.url
            except:
                pass
        
        # Fetch the page
        r = requests.get(actual_url, timeout=timeout, allow_redirects=True, headers=HEADERS)
        r.raise_for_status()
        
        content_length = len(r.text)
        soup = BeautifulSoup(r.text, "lxml")
        page_text = soup.get_text().lower()
        
        # Check 1: Look for paywall keywords in page text
        for keyword in PAYWALL_KEYWORDS:
            if keyword in page_text:
                # Count occurrences to determine confidence
                count = page_text.count(keyword)
                if count >= 2:  # Multiple occurrences suggest paywall
                    return True, f"Keyword: {keyword} (found {count} times)", content_length
        
        # Check 2: Look for paywall-related CSS selectors
        for selector in PAYWALL_SELECTORS:
            elements = soup.select(selector)
            if elements:
                return True, f"CSS selector: {selector}", content_length
        
        # Check 3: Check meta tags
        for meta_name in PAYWALL_META_TAGS:
            # Check meta name
            meta = soup.find("meta", {"name": meta_name})
            if meta:
                return True, f"Meta tag: {meta_name}", content_length
            
            # Check meta property
            meta = soup.find("meta", {"property": f"og:{meta_name}"})
            if meta:
                return True, f"Meta property: og:{meta_name}", content_length
        
        # Check 4: Look for subscription prompts in common locations
        # Check for common subscription button/link text
        subscription_texts = [
            "subscribe",
            "sign in",
            "create account",
            "join now",
            "become a member",
        ]
        
        for text in subscription_texts:
            # Look for links or buttons with subscription text
            elements = soup.find_all(["a", "button"], string=lambda s: s and text in s.lower())
            if len(elements) >= 2:  # Multiple subscription prompts suggest paywall
                return True, f"Subscription prompts: {text}", content_length
        
        # Check 5: Check article content length
        # Paywalled articles often show only a preview (first few paragraphs)
        article_selectors = [
            "article",
            "[role='article']",
            ".article-body",
            ".article-content",
            "[class*='article']",
        ]
        
        article_text_length = 0
        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                article_text = article.get_text()
                article_text_length = len(article_text)
                break
        
        # If article is very short (< 500 chars), might be paywalled
        if article_text_length > 0 and article_text_length < 500:
            return True, f"Short article content: {article_text_length} chars", content_length
        
        # Check 6: Look for "read more" or "continue reading" links
        # These often indicate truncated content
        read_more_texts = ["read more", "continue reading", "read full article"]
        for text in read_more_texts:
            elements = soup.find_all(string=lambda s: s and text.lower() in s.lower())
            if elements:
                # Check if there's a paywall-related link nearby
                for elem in elements[:3]:  # Check first few occurrences
                    parent = elem.parent
                    if parent and parent.name == "a":
                        href = parent.get("href", "")
                        if any(keyword in href.lower() for keyword in ["subscribe", "sign", "join", "member"]):
                            return True, f"Read more link with subscription: {text}", content_length
        
        # Check 7: Domain-specific paywall detection
        domain = actual_url.split("/")[2] if "/" in actual_url else ""
        
        # New York Times specific
        if "nytimes.com" in domain:
            # NYT often uses specific classes
            if soup.select_one("[class*='paywall']") or soup.select_one("[data-testid='paywall']"):
                return True, "NYT paywall detected", content_length
        
        # Washington Post specific
        if "washingtonpost.com" in domain:
            if soup.select_one("[class*='paywall']") or soup.select_one("[data-qa='paywall']"):
                return True, "WP paywall detected", content_length
        
        # The Guardian specific
        if "theguardian.com" in domain:
            # Guardian has a "premium" indicator
            if soup.select_one("[class*='premium']") or "premium" in page_text[:2000]:
                return True, "Guardian premium content", content_length
        
        # If no paywall indicators found, assume free
        return False, "free", content_length
        
    except requests.exceptions.Timeout:
        return None, "timeout", 0
    except requests.exceptions.RequestException as e:
        return None, f"error: {str(e)[:50]}", 0
    except Exception as e:
        return None, f"error: {str(e)[:50]}", 0


def check_urls_from_file(url_file: str, output_file: str = None, max_urls: int = None) -> Dict[str, int]:
    """
    Check paywall status for URLs in a file
    
    Args:
        url_file: Path to file containing URLs (one per line)
        output_file: Optional output file to save results
        max_urls: Maximum number of URLs to check (None for all)
        
    Returns:
        Dictionary with statistics
    """
    if not os.path.exists(url_file):
        print(f"Error: File not found: {url_file}")
        return {}
    
    # Read URLs
    with open(url_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if max_urls:
        urls = urls[:max_urls]
    
    print(f"\nChecking {len(urls)} URLs from {url_file}...")
    
    # Results
    paywall_urls = []
    free_urls = []
    error_urls = []
    
    # Check each URL
    for url in tqdm(urls, desc="Checking paywalls"):
        has_paywall, reason, content_length = check_paywall(url)
        
        if has_paywall is True:
            paywall_urls.append((url, reason, content_length))
        elif has_paywall is False:
            free_urls.append((url, reason, content_length))
        else:
            error_urls.append((url, reason, content_length))
        
        time.sleep(0.5)  # Be polite
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Paywall Check Results for {os.path.basename(url_file)}")
    print(f"{'='*60}")
    print(f"Total URLs checked: {len(urls)}")
    print(f"Free articles: {len(free_urls)} ({len(free_urls)/len(urls)*100:.1f}%)")
    print(f"Paywalled articles: {len(paywall_urls)} ({len(paywall_urls)/len(urls)*100:.1f}%)")
    print(f"Errors: {len(error_urls)} ({len(error_urls)/len(urls)*100:.1f}%)")
    print(f"{'='*60}")
    
    # Save results if output file specified
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Free Articles\n")
            for url, reason, length in free_urls:
                f.write(f"{url}\n")
            
            f.write("\n# Paywalled Articles\n")
            for url, reason, length in paywall_urls:
                f.write(f"{url} # {reason}\n")
            
            f.write("\n# Errors\n")
            for url, reason, length in error_urls:
                f.write(f"{url} # {reason}\n")
        
        print(f"\nResults saved to {output_file}")
    
    return {
        "total": len(urls),
        "free": len(free_urls),
        "paywall": len(paywall_urls),
        "errors": len(error_urls)
    }


def check_all_media_urls(data_dir: str = "lunar_2026_data", max_per_media: int = None):
    """
    Check paywall status for all media URL files
    
    Args:
        data_dir: Directory containing URL files
        max_per_media: Maximum URLs to check per media (None for all)
    """
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from news_media_config import NEWS_MEDIA_CONFIG
    
    print("="*60)
    print("Paywall Checker for All Media")
    print("="*60)
    
    all_stats = {}
    
    for media_name, config in NEWS_MEDIA_CONFIG.items():
        code = config["code"]
        url_file = os.path.join(data_dir, f"{code}.txt")
        
        if not os.path.exists(url_file):
            print(f"\nSkipping {media_name}: {url_file} not found")
            continue
        
        output_file = os.path.join(data_dir, f"{code}_paywall_check.txt")
        stats = check_urls_from_file(url_file, output_file, max_per_media)
        all_stats[media_name] = stats
    
    # Print overall summary
    print("\n" + "="*60)
    print("Overall Summary")
    print("="*60)
    
    total_urls = sum(s.get("total", 0) for s in all_stats.values())
    total_free = sum(s.get("free", 0) for s in all_stats.values())
    total_paywall = sum(s.get("paywall", 0) for s in all_stats.values())
    total_errors = sum(s.get("errors", 0) for s in all_stats.values())
    
    print(f"Total URLs checked: {total_urls}")
    print(f"Free articles: {total_free} ({total_free/total_urls*100:.1f}%)" if total_urls > 0 else "Free articles: 0")
    print(f"Paywalled articles: {total_paywall} ({total_paywall/total_urls*100:.1f}%)" if total_urls > 0 else "Paywalled articles: 0")
    print(f"Errors: {total_errors} ({total_errors/total_urls*100:.1f}%)" if total_urls > 0 else "Errors: 0")
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check paywall status for article URLs")
    parser.add_argument(
        "--file",
        type=str,
        help="Check URLs from a specific file"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results"
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Maximum number of URLs to check"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all media URL files"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="lunar_2026_data",
        help="Directory containing URL files (default: lunar_2026_data)"
    )
    
    args = parser.parse_args()
    
    if args.all:
        check_all_media_urls(args.data_dir, args.max)
    elif args.file:
        check_urls_from_file(args.file, args.output, args.max)
    else:
        print("Please specify --file <url_file> or --all")
        print("\nExamples:")
        print("  python crawlers/check_paywall.py --file lunar_2026_data/cnn.txt")
        print("  python crawlers/check_paywall.py --all")
        print("  python crawlers/check_paywall.py --all --max 10")

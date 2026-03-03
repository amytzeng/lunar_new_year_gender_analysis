"""
Multi-news crawler for Lunar New Year related articles
Crawls articles from multiple international news media sources
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import argparse
from datetime import datetime
from typing import List, Dict, Set, Tuple
from tqdm import tqdm
from collections import defaultdict

import sys
import os

# Add crawlers directory to path for imports when running as script
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from news_media_config import NEWS_MEDIA_CONFIG, LUNAR_NEW_YEAR_KEYWORDS
from utils.article_extractor import fetch_article_content, extract_title_from_html, extract_actual_url_from_google_news


def search_google_news_rss(
    keyword: str,
    site_domain: str,
    start_date: str,
    end_date: str,
    max_articles: int = 100
) -> List[Dict[str, str]]:
    """
    Search for articles using Google News RSS feed
    
    Args:
        keyword: Search keyword
        site_domain: Domain to search (e.g., "cnn.com")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_articles: Maximum number of articles to return
        
    Returns:
        List of dictionaries containing title, link, and pub_date
    """
    base_url = "https://news.google.com/rss/search"
    query = f"{keyword}+site:{site_domain}"
    url = f"{base_url}?q={query}+after:{start_date}+before:{end_date}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")
        
        results = []
        for item in items[:max_articles]:
            link = item.link.text
            title = item.title.text
            pub_date = item.pubDate.text if item.pubDate else ""
            
            # Google News RSS returns encoded URLs in format:
            # https://news.google.com/rss/articles/CBMi...
            # These need to be decoded to get the actual article URL
            # We'll extract the actual URL when fetching content
            results.append({
                "title": title,
                "link": link,  # Keep original link, extract actual URL when fetching
                "pub_date": pub_date
            })
        
        return results
    except Exception as e:
        print(f"Error fetching Google News RSS for {site_domain} with keyword '{keyword}': {e}")
        return []


def deduplicate_articles(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate articles based on URL
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Deduplicated list of articles
    """
    seen_urls: Set[str] = set()
    unique_articles = []
    
    for article in articles:
        url = article.get("link", "")
        # Normalize URL by removing query parameters and fragments
        normalized_url = url.split("?")[0].split("#")[0]
        if normalized_url not in seen_urls:
            seen_urls.add(normalized_url)
            unique_articles.append(article)
    
    return unique_articles


def save_article_to_file(
    article: Dict[str, str],
    article_id: str,
    media_code: str,
    matched_keyword: str,
    output_dir: str,
    file_number: int
) -> bool:
    """
    Save article to a text file in the format required by the classification script
    
    Args:
        article: Dictionary containing article data (title, link, pub_date, content)
        article_id: Unique article identifier
        media_code: Media source code
        matched_keyword: Keyword that matched this article
        output_dir: Output directory path
        file_number: Sequential file number for naming
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # File name format: {number}.txt (e.g., 1.txt, 2.txt)
        filename = f"{file_number}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # Extract date from pub_date or use current date
        date_str = article.get("pub_date", "")
        if date_str:
            try:
                # Parse RSS date format (e.g., "Mon, 17 Feb 2026 12:00:00 GMT")
                # Try simple parsing first
                if "," in date_str:
                    # Format: "Mon, 17 Feb 2026 12:00:00 GMT"
                    parts = date_str.split(",")
                    if len(parts) >= 2:
                        date_part = parts[1].strip().split()[0:3]  # Get day, month, year
                        if len(date_part) == 3:
                            day, month, year = date_part
                            month_map = {
                                "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                                "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                                "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
                            }
                            month_num = month_map.get(month, "01")
                            date_str = f"{year}-{month_num}-{day.zfill(2)}"
                        else:
                            date_str = datetime.now().strftime("%Y-%m-%d")
                    else:
                        date_str = datetime.now().strftime("%Y-%m-%d")
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Write article to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"article_id: {article_id}\n")
            f.write(f"url: {article.get('link', '')}\n")
            f.write(f"title: {article.get('title', 'Article')}\n")
            f.write(f"date: {date_str}\n")
            f.write(f"author: \n")
            f.write(f"matched_keywords: {matched_keyword}\n")
            f.write(f"content:\n")
            f.write(article.get("content", ""))
        
        return True
    except Exception as e:
        print(f"Error saving article {article_id}: {e}")
        return False


def crawl_media_urls_only(
    media_name: str,
    keywords: List[str],
    start_date: str,
    end_date: str,
    output_dir: str,
    max_articles_per_keyword: int = 50,
    delay: float = 1.0
) -> Dict[str, int]:
    """
    Crawl article URLs only from a specific media source (no content fetching)
    
    Args:
        media_name: Media name from config (e.g., "cnn", "bbc")
        keywords: List of keywords to search
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_dir: Output directory for saved URL files
        max_articles_per_keyword: Maximum articles to fetch per keyword
        delay: Delay between requests in seconds
        
    Returns:
        Statistics dictionary
    """
    if media_name not in NEWS_MEDIA_CONFIG:
        print(f"Unknown media: {media_name}")
        return {"total_found": 0, "total_saved": 0}
    
    config = NEWS_MEDIA_CONFIG[media_name]
    domain = config["domain"]
    code = config["code"]
    
    print(f"\n{'='*60}")
    print(f"Crawling {media_name.upper()} ({domain})")
    print(f"{'='*60}")
    
    all_articles = []
    
    # Search for each keyword
    for keyword in keywords:
        print(f"\nSearching for: '{keyword}'")
        articles = search_google_news_rss(
            keyword=keyword,
            site_domain=domain,
            start_date=start_date,
            end_date=end_date,
            max_articles=max_articles_per_keyword
        )
        
        all_articles.extend(articles)
        print(f"Found {len(articles)} articles")
        time.sleep(delay)  # Be polite to Google News
    
    # Deduplicate articles
    print(f"\nTotal articles found: {len(all_articles)}")
    unique_articles = deduplicate_articles(all_articles)
    print(f"Unique articles after deduplication: {len(unique_articles)}")
    
    # Save URLs to file (one URL per line)
    output_file = os.path.join(output_dir, f"{code}.txt")
    os.makedirs(output_dir, exist_ok=True)
    
    saved_count = 0
    seen_urls = set()
    
    print(f"\nSaving URLs to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        for article in unique_articles:
            url = article.get("link", "")
            if url:
                # Normalize URL for deduplication
                normalized_url = url.split("?")[0].split("#")[0]
                if normalized_url not in seen_urls:
                    f.write(f"{url}\n")
                    seen_urls.add(normalized_url)
                    saved_count += 1
    
    stats = {
        "total_found": len(unique_articles),
        "total_saved": saved_count
    }
    
    print(f"\n{media_name.upper()} Summary:")
    print(f"  Found: {stats['total_found']} articles")
    print(f"  Saved: {stats['total_saved']} URLs to {output_file}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Crawl Lunar New Year related articles from multiple news media"
    )
    parser.add_argument(
        "--media",
        nargs="+",
        default=list(NEWS_MEDIA_CONFIG.keys()),
        help="Media sources to crawl (default: all)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2026-02-01",
        help="Start date in YYYY-MM-DD format (default: 2026-02-01)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2026-02-28",
        help="End date in YYYY-MM-DD format (default: 2026-02-28)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="lunar_2026_data",
        help="Output directory for articles (default: lunar_2026_data)"
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=LUNAR_NEW_YEAR_KEYWORDS,
        help="Keywords to search (default: predefined Lunar New Year keywords)"
    )
    parser.add_argument(
        "--max-per-keyword",
        type=int,
        default=50,
        help="Maximum articles per keyword (default: 50)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Multi-News Crawler for Lunar New Year Articles")
    print("="*60)
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Media sources: {', '.join(args.media)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Keywords: {len(args.keywords)} keywords")
    print("="*60)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Crawl each media source (URLs only)
    all_stats = defaultdict(int)
    
    for media_name in args.media:
        if media_name not in NEWS_MEDIA_CONFIG:
            print(f"\nWarning: Unknown media '{media_name}', skipping...")
            continue
        
        stats = crawl_media_urls_only(
            media_name=media_name,
            keywords=args.keywords,
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=args.output_dir,
            max_articles_per_keyword=args.max_per_keyword,
            delay=args.delay
        )
        
        for key, value in stats.items():
            all_stats[key] += value
    
    # Print final summary
    print("\n" + "="*60)
    print("Final Summary")
    print("="*60)
    print(f"Total URLs found: {all_stats['total_found']}")
    print(f"Total URLs saved: {all_stats['total_saved']}")
    print(f"\nURL files saved to {args.output_dir}/:")
    for media_name in args.media:
        if media_name in NEWS_MEDIA_CONFIG:
            code = NEWS_MEDIA_CONFIG[media_name]["code"]
            url_file = os.path.join(args.output_dir, f"{code}.txt")
            if os.path.exists(url_file):
                with open(url_file, "r", encoding="utf-8") as f:
                    url_count = len([line for line in f if line.strip()])
                print(f"  - {code}.txt: {url_count} URLs")
    print("="*60)


if __name__ == "__main__":
    main()

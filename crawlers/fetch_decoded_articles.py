"""
Fetch articles from decoded URLs
Reads all *_decoded.txt files and fetches article content from decoded URLs
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
from tqdm import tqdm
import time

# Add crawlers directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from news_media_config import NEWS_MEDIA_CONFIG
from utils.article_extractor import fetch_article_content, extract_title_from_html


def identify_media_from_url(url: str) -> Optional[Dict[str, any]]:
    """
    Identify news media source from URL domain
    
    Args:
        url: Article URL
        
    Returns:
        Media configuration dictionary if found, None otherwise
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Match domain with media config
        for media_name, config in NEWS_MEDIA_CONFIG.items():
            config_domain = config["domain"].lower()
            if config_domain in domain or domain.endswith('.' + config_domain):
                return config
        
        return None
    except Exception:
        return None


def extract_url_from_line(line: str) -> Optional[str]:
    """
    Extract URL from a line, handling both successful and failed URLs
    
    Args:
        line: Line from decoded file
        
    Returns:
        URL if found and valid, None if failed or invalid
    """
    line = line.strip()
    
    # Skip empty lines
    if not line:
        return None
    
    # Skip failed URLs (contain "# Failed to decode")
    if "# Failed to decode" in line:
        return None
    
    # Extract URL (everything before any comment or whitespace)
    # Pattern: URL at the start of line, possibly followed by comment
    match = re.match(r'^(https?://[^\s#]+)', line)
    if match:
        url = match.group(1)
        # Basic URL validation
        if url.startswith('http://') or url.startswith('https://'):
            return url
    
    return None


def save_article_to_file(
    article_url: str,
    article_title: str,
    article_content: str,
    media_code: str,
    output_dir: str,
    file_number: int
) -> bool:
    """
    Save article to a text file in the format required by the classification script
    
    Args:
        article_url: Article URL
        article_title: Article title
        article_content: Article content
        media_code: Media source code
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
        
        # Use current date as publication date
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Generate article ID
        article_id = f"{media_code}_{file_number}"
        
        # Write article to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"article_id: {article_id}\n")
            f.write(f"url: {article_url}\n")
            f.write(f"title: {article_title}\n")
            f.write(f"date: {date_str}\n")
            f.write(f"author: \n")
            f.write(f"matched_keywords: Lunar New Year\n")
            f.write(f"content:\n")
            f.write(article_content)
        
        return True
    except Exception as e:
        print(f"Error saving article {file_number}: {e}")
        return False


def get_next_file_number(output_dir: str) -> int:
    """
    Get the next file number for a media directory
    
    Args:
        output_dir: Output directory for the media
        
    Returns:
        Next file number (1 if directory doesn't exist or is empty)
    """
    if not os.path.exists(output_dir):
        return 1
    
    # Find existing files
    existing_files = [
        f for f in os.listdir(output_dir)
        if f.endswith('.txt') and f[:-4].isdigit()
    ]
    
    if not existing_files:
        return 1
    
    # Get maximum file number
    max_num = max(int(f[:-4]) for f in existing_files)
    return max_num + 1


def process_decoded_file(
    decoded_file: str,
    output_base_dir: str,
    delay: float = 1.0
) -> Dict[str, any]:
    """
    Process a decoded file and fetch articles
    
    Args:
        decoded_file: Path to the decoded file
        output_base_dir: Base directory for output files
        delay: Delay between requests in seconds
        
    Returns:
        Dictionary with statistics
    """
    stats = {
        "total_lines": 0,
        "skipped_failed": 0,
        "skipped_invalid": 0,
        "skipped_no_media": 0,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    # Track file numbers per media
    media_file_numbers = {}
    
    # Read the file
    try:
        with open(decoded_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {decoded_file}: {e}")
        stats["errors"].append(f"Error reading file: {e}")
        return stats
    
    stats["total_lines"] = len(lines)
    
    # Process each line
    for line_num, line in enumerate(lines, 1):
        # Extract URL
        url = extract_url_from_line(line)
        
        if url is None:
            # Check why it was skipped
            if "# Failed to decode" in line:
                stats["skipped_failed"] += 1
            else:
                stats["skipped_invalid"] += 1
            continue
        
        # Identify media source
        media_config = identify_media_from_url(url)
        if not media_config:
            stats["skipped_no_media"] += 1
            continue
        
        stats["processed"] += 1
        
        # Fetch article content
        try:
            # Get selectors for this media
            selectors = media_config.get("selectors", [])
            
            # Fetch content
            content = fetch_article_content(url, selectors)
            
            # Check if content was successfully fetched
            if content.startswith("[Error") or content.startswith("[No article"):
                stats["failed"] += 1
                stats["errors"].append(f"Line {line_num}: Failed to fetch content from {url}")
                continue
            
            # Extract title
            title = extract_title_from_html(url)
            if not title or title == "Article":
                # Try to extract from URL or use default
                title = url.split('/')[-1].replace('-', ' ').title() or "Article"
            
            # Determine output directory
            media_code = media_config["code"]
            output_dir = os.path.join(output_base_dir, media_code)
            
            # Get next file number for this media
            if media_code not in media_file_numbers:
                media_file_numbers[media_code] = get_next_file_number(output_dir)
            file_number = media_file_numbers[media_code]
            
            # Save article
            if save_article_to_file(
                article_url=url,
                article_title=title,
                article_content=content,
                media_code=media_code,
                output_dir=output_dir,
                file_number=file_number
            ):
                stats["success"] += 1
                media_file_numbers[media_code] += 1
            else:
                stats["failed"] += 1
                stats["errors"].append(f"Line {line_num}: Failed to save article from {url}")
            
            # Delay between requests
            if delay > 0:
                time.sleep(delay)
                
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"Line {line_num}: Error processing {url}: {e}")
    
    return stats


def process_directory(
    input_dir: str,
    output_dir: str,
    delay: float = 1.0
) -> Dict[str, any]:
    """
    Process all *_decoded.txt files in a directory
    
    Args:
        input_dir: Directory containing decoded files
        output_dir: Output directory for articles
        delay: Delay between requests in seconds
        
    Returns:
        Dictionary with overall statistics
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Directory {input_dir} does not exist")
        return {}
    
    # Find all *_decoded.txt files (excluding backup files)
    decoded_files = [
        f for f in input_path.glob("*_decoded.txt")
        if not f.name.endswith(".backup")
    ]
    
    if not decoded_files:
        print(f"No *_decoded.txt files found in {input_dir}")
        return {}
    
    print(f"Found {len(decoded_files)} decoded files to process")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each file
    all_stats = {
        "total_files": len(decoded_files),
        "total_lines": 0,
        "total_skipped_failed": 0,
        "total_skipped_invalid": 0,
        "total_skipped_no_media": 0,
        "total_processed": 0,
        "total_success": 0,
        "total_failed": 0,
        "file_stats": {},
        "all_errors": []
    }
    
    for decoded_file in tqdm(decoded_files, desc="Processing files"):
        # Process file
        stats = process_decoded_file(
            str(decoded_file),
            output_dir,
            delay=delay
        )
        
        # Update overall statistics
        all_stats["total_lines"] += stats["total_lines"]
        all_stats["total_skipped_failed"] += stats["skipped_failed"]
        all_stats["total_skipped_invalid"] += stats["skipped_invalid"]
        all_stats["total_skipped_no_media"] += stats["skipped_no_media"]
        all_stats["total_processed"] += stats["processed"]
        all_stats["total_success"] += stats["success"]
        all_stats["total_failed"] += stats["failed"]
        all_stats["file_stats"][decoded_file.name] = stats
        all_stats["all_errors"].extend(stats["errors"])
    
    return all_stats


def print_summary(stats: Dict[str, any]):
    """
    Print processing summary statistics
    
    Args:
        stats: Statistics dictionary from process_directory
    """
    print("\n" + "=" * 60)
    print("Fetching Summary")
    print("=" * 60)
    print(f"Total files processed: {stats['total_files']}")
    print(f"Total lines read: {stats['total_lines']}")
    print(f"Skipped (failed decode): {stats['total_skipped_failed']}")
    print(f"Skipped (invalid URL): {stats['total_skipped_invalid']}")
    print(f"Skipped (no media match): {stats['total_skipped_no_media']}")
    print(f"Total URLs processed: {stats['total_processed']}")
    print(f"Successfully fetched: {stats['total_success']}")
    print(f"Failed to fetch: {stats['total_failed']}")
    
    if stats['total_processed'] > 0:
        success_rate = (stats['total_success'] / stats['total_processed']) * 100
        print(f"Success rate: {success_rate:.2f}%")
    
    print("\nPer-file statistics:")
    print("-" * 60)
    for filename, file_stats in stats['file_stats'].items():
        if file_stats['processed'] > 0:
            print(f"{filename}:")
            print(f"  Processed: {file_stats['processed']}")
            print(f"  Success: {file_stats['success']}")
            print(f"  Failed: {file_stats['failed']}")
            print(f"  Skipped (failed decode): {file_stats['skipped_failed']}")
    
    if stats['all_errors']:
        print(f"\nErrors encountered: {len(stats['all_errors'])}")
        if len(stats['all_errors']) <= 10:
            print("First few errors:")
            for error in stats['all_errors'][:10]:
                print(f"  - {error}")
        else:
            print(f"First 10 errors (out of {len(stats['all_errors'])}):")
            for error in stats['all_errors'][:10]:
                print(f"  - {error}")
    
    print("=" * 60)


def main():
    """
    Main entry point for the fetch script
    """
    parser = argparse.ArgumentParser(
        description="Fetch articles from decoded Google News URLs"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="lunar_2026_data",
        help="Input directory containing *_decoded.txt files (default: lunar_2026_data)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="lunar_2026_articles",
        help="Output directory for fetched articles (default: lunar_2026_articles)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    # Determine paths (relative to script location or absolute)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if os.path.isabs(args.input_dir):
        input_dir = args.input_dir
    else:
        input_dir = os.path.join(project_root, args.input_dir)
    
    if os.path.isabs(args.output_dir):
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(project_root, args.output_dir)
    
    print("=" * 60)
    print("Article Fetcher from Decoded URLs")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Delay between requests: {args.delay} seconds")
    print("=" * 60)
    
    # Process directory
    stats = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        delay=args.delay
    )
    
    # Print summary
    if stats:
        print_summary(stats)
    else:
        print("No files were processed.")


if __name__ == "__main__":
    main()

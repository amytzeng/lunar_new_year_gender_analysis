"""
Batch decoder for Google News URLs
Processes all .txt files in a directory and decodes Google News URLs to actual article URLs
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from tqdm import tqdm

# Add crawlers directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.google_news_decoder import decode_google_news_url


def process_file(input_file: str, output_file: str, use_fallback: bool = True) -> Dict[str, int]:
    """
    Process a single file and decode all Google News URLs
    
    Args:
        input_file: Path to input file containing Google News URLs
        output_file: Path to output file for decoded URLs
        use_fallback: Whether to use requests method if decoder fails
        
    Returns:
        Dictionary with statistics:
            - total: Total URLs processed
            - success: Successfully decoded URLs
            - failed: Failed to decode URLs
            - skipped: Skipped lines (empty or invalid)
    """
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0
    }
    
    failed_urls = []
    
    # Read input file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        return stats
    
    # Process each line
    decoded_urls = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            stats["skipped"] += 1
            continue
        
        stats["total"] += 1
        
        # Decode URL
        result = decode_google_news_url(line, use_fallback=use_fallback)
        
        if result["success"]:
            decoded_urls.append(result["decoded_url"])
            stats["success"] += 1
        else:
            # Keep original URL and add comment
            decoded_urls.append(f"{result['decoded_url']}  # Failed to decode: {result['error']}")
            stats["failed"] += 1
            failed_urls.append({
                "line": line_num,
                "url": line,
                "error": result["error"],
                "method": result["method"]
            })
    
    # Write output file
    try:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for url in decoded_urls:
                f.write(f"{url}\n")
    except Exception as e:
        print(f"Error writing file {output_file}: {e}")
        return stats
    
    # Store failed URLs for logging
    stats["failed_urls"] = failed_urls
    
    return stats


def process_directory(
    input_dir: str,
    output_suffix: str = "_decoded",
    use_fallback: bool = True,
    log_file: Optional[str] = None
) -> Dict[str, any]:
    """
    Process all .txt files in a directory
    
    Args:
        input_dir: Directory containing input .txt files
        output_suffix: Suffix to add to output filenames (default: "_decoded")
        use_fallback: Whether to use requests method if decoder fails
        log_file: Optional path to log file for failed URLs
        
    Returns:
        Dictionary with overall statistics
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Directory {input_dir} does not exist")
        return {}
    
    # Find all .txt files (excluding already decoded files)
    txt_files = [
        f for f in input_path.glob("*.txt")
        if not f.name.endswith(f"{output_suffix}.txt")
    ]
    
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return {}
    
    print(f"Found {len(txt_files)} files to process")
    print("=" * 60)
    
    # Process each file
    all_stats = {
        "total_files": len(txt_files),
        "total_urls": 0,
        "total_success": 0,
        "total_failed": 0,
        "total_skipped": 0,
        "file_stats": {},
        "all_failed_urls": []
    }
    
    for txt_file in tqdm(txt_files, desc="Processing files"):
        # Generate output filename
        output_file = txt_file.parent / f"{txt_file.stem}{output_suffix}.txt"
        
        # Process file
        stats = process_file(str(txt_file), str(output_file), use_fallback=use_fallback)
        
        # Update overall statistics
        all_stats["total_urls"] += stats["total"]
        all_stats["total_success"] += stats["success"]
        all_stats["total_failed"] += stats["failed"]
        all_stats["total_skipped"] += stats["skipped"]
        all_stats["file_stats"][txt_file.name] = stats
        
        # Collect failed URLs
        if "failed_urls" in stats:
            for failed in stats["failed_urls"]:
                failed["file"] = txt_file.name
                all_stats["all_failed_urls"].append(failed)
    
    # Write log file if specified
    if log_file and all_stats["all_failed_urls"]:
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"Google News URL Decoding Log\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                for failed in all_stats["all_failed_urls"]:
                    f.write(f"File: {failed['file']}\n")
                    f.write(f"Line: {failed['line']}\n")
                    f.write(f"URL: {failed['url']}\n")
                    f.write(f"Error: {failed['error']}\n")
                    f.write(f"Method: {failed['method']}\n")
                    f.write("-" * 60 + "\n\n")
        except Exception as e:
            print(f"Error writing log file {log_file}: {e}")
    
    return all_stats


def print_summary(stats: Dict[str, any]):
    """
    Print processing summary statistics
    
    Args:
        stats: Statistics dictionary from process_directory
    """
    print("\n" + "=" * 60)
    print("Processing Summary")
    print("=" * 60)
    print(f"Total files processed: {stats['total_files']}")
    print(f"Total URLs processed: {stats['total_urls']}")
    print(f"Successfully decoded: {stats['total_success']}")
    print(f"Failed to decode: {stats['total_failed']}")
    print(f"Skipped (empty lines): {stats['total_skipped']}")
    
    if stats['total_urls'] > 0:
        success_rate = (stats['total_success'] / stats['total_urls']) * 100
        print(f"Success rate: {success_rate:.2f}%")
    
    print("\nPer-file statistics:")
    print("-" * 60)
    for filename, file_stats in stats['file_stats'].items():
        print(f"{filename}:")
        print(f"  Total: {file_stats['total']}")
        print(f"  Success: {file_stats['success']}")
        print(f"  Failed: {file_stats['failed']}")
        print(f"  Skipped: {file_stats['skipped']}")
    
    if stats['all_failed_urls']:
        print(f"\nFailed URLs logged: {len(stats['all_failed_urls'])}")
    
    print("=" * 60)


def main():
    """
    Main entry point for the batch decoder script
    """
    parser = argparse.ArgumentParser(
        description="Batch decode Google News URLs to actual article URLs"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="lunar_2026_data",
        help="Input directory containing .txt files with Google News URLs (default: lunar_2026_data)"
    )
    parser.add_argument(
        "--output-suffix",
        type=str,
        default="_decoded",
        help="Suffix for output filenames (default: _decoded)"
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Disable fallback to requests method (only use googlenewsdecoder)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file for failed URLs (default: None)"
    )
    
    args = parser.parse_args()
    
    # Determine input directory (relative to script location or absolute)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if os.path.isabs(args.input_dir):
        input_dir = args.input_dir
    else:
        input_dir = os.path.join(project_root, args.input_dir)
    
    # Determine log file path
    log_file = None
    if args.log_file:
        if os.path.isabs(args.log_file):
            log_file = args.log_file
        else:
            log_file = os.path.join(project_root, args.log_file)
    
    print("=" * 60)
    print("Google News URL Batch Decoder")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Output suffix: {args.output_suffix}")
    print(f"Fallback enabled: {not args.no_fallback}")
    if log_file:
        print(f"Log file: {log_file}")
    print("=" * 60)
    
    # Process directory
    stats = process_directory(
        input_dir=input_dir,
        output_suffix=args.output_suffix,
        use_fallback=not args.no_fallback,
        log_file=log_file
    )
    
    # Print summary
    if stats:
        print_summary(stats)
    else:
        print("No files were processed.")


if __name__ == "__main__":
    main()

"""
Retry script for failed Google News URL decoding
Processes *_decoded.txt files and retries decoding failed URLs using enhanced methods
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from tqdm import tqdm

# Add crawlers directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.google_news_decoder import decode_google_news_url


def extract_original_url(failed_line: str) -> Optional[str]:
    """
    Extract the original Google News URL from a failed line
    
    Args:
        failed_line: Line containing failed URL with error comment
        
    Returns:
        Original Google News URL if found, None otherwise
    """
    # Pattern: URL followed by "# Failed to decode: ..."
    # Example: "https://news.google.com/... # Failed to decode: ..."
    match = re.match(r'^(https://[^\s#]+)', failed_line.strip())
    if match:
        return match.group(1)
    return None


def process_decoded_file(decoded_file: str, use_enhanced: bool = True) -> Dict[str, any]:
    """
    Process a decoded file and retry failed URLs
    
    Args:
        decoded_file: Path to the decoded file
        use_enhanced: Whether to use enhanced parsing method
        
    Returns:
        Dictionary with statistics:
            - total_lines: Total lines in file
            - failed_lines: Number of failed lines found
            - retried: Number of URLs retried
            - success: Number of successful retries
            - still_failed: Number of URLs that still failed
            - updated_lines: List of updated lines
    """
    stats = {
        "total_lines": 0,
        "failed_lines": 0,
        "retried": 0,
        "success": 0,
        "still_failed": 0,
        "updated_lines": []
    }
    
    # Read the file
    try:
        with open(decoded_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {decoded_file}: {e}")
        return stats
    
    stats["total_lines"] = len(lines)
    
    # Process each line
    for line_num, line in enumerate(lines):
        line = line.rstrip('\n\r')
        
        # Check if this is a failed line
        if "# Failed to decode" in line:
            stats["failed_lines"] += 1
            
            # Extract original URL
            original_url = extract_original_url(line)
            if not original_url:
                # If we can't extract the URL, keep the line as is
                stats["updated_lines"].append(line)
                continue
            
            stats["retried"] += 1
            
            # Retry decoding with enhanced method
            result = decode_google_news_url(
                original_url,
                use_fallback=True,
                use_enhanced=use_enhanced
            )
            
            if result["success"]:
                # Success! Replace with decoded URL
                stats["updated_lines"].append(result["decoded_url"])
                stats["success"] += 1
            else:
                # Still failed, keep original line
                stats["updated_lines"].append(line)
                stats["still_failed"] += 1
        else:
            # This is a successful line, keep it as is
            stats["updated_lines"].append(line)
    
    return stats


def process_directory(
    input_dir: str,
    use_enhanced: bool = True,
    backup: bool = True
) -> Dict[str, any]:
    """
    Process all *_decoded.txt files in a directory
    
    Args:
        input_dir: Directory containing decoded files
        use_enhanced: Whether to use enhanced parsing method
        backup: Whether to create backup files before updating
        
    Returns:
        Dictionary with overall statistics
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Directory {input_dir} does not exist")
        return {}
    
    # Find all *_decoded.txt files
    decoded_files = list(input_path.glob("*_decoded.txt"))
    
    if not decoded_files:
        print(f"No *_decoded.txt files found in {input_dir}")
        return {}
    
    print(f"Found {len(decoded_files)} decoded files to process")
    print("=" * 60)
    
    # Process each file
    all_stats = {
        "total_files": len(decoded_files),
        "total_failed_lines": 0,
        "total_retried": 0,
        "total_success": 0,
        "total_still_failed": 0,
        "file_stats": {}
    }
    
    for decoded_file in tqdm(decoded_files, desc="Processing files"):
        # Create backup if requested
        if backup:
            backup_file = decoded_file.with_suffix('.txt.backup')
            try:
                import shutil
                shutil.copy2(decoded_file, backup_file)
            except Exception as e:
                print(f"Warning: Could not create backup for {decoded_file.name}: {e}")
        
        # Process file
        stats = process_decoded_file(str(decoded_file), use_enhanced=use_enhanced)
        
        # Update overall statistics
        all_stats["total_failed_lines"] += stats["failed_lines"]
        all_stats["total_retried"] += stats["retried"]
        all_stats["total_success"] += stats["success"]
        all_stats["total_still_failed"] += stats["still_failed"]
        all_stats["file_stats"][decoded_file.name] = stats
        
        # Write updated file
        if stats["retried"] > 0:
            try:
                with open(decoded_file, "w", encoding="utf-8") as f:
                    for updated_line in stats["updated_lines"]:
                        f.write(f"{updated_line}\n")
            except Exception as e:
                print(f"Error writing file {decoded_file.name}: {e}")
    
    return all_stats


def print_summary(stats: Dict[str, any]):
    """
    Print processing summary statistics
    
    Args:
        stats: Statistics dictionary from process_directory
    """
    print("\n" + "=" * 60)
    print("Retry Summary")
    print("=" * 60)
    print(f"Total files processed: {stats['total_files']}")
    print(f"Total failed lines found: {stats['total_failed_lines']}")
    print(f"Total URLs retried: {stats['total_retried']}")
    print(f"Successfully decoded: {stats['total_success']}")
    print(f"Still failed: {stats['total_still_failed']}")
    
    if stats['total_retried'] > 0:
        success_rate = (stats['total_success'] / stats['total_retried']) * 100
        print(f"Retry success rate: {success_rate:.2f}%")
    
    print("\nPer-file statistics:")
    print("-" * 60)
    for filename, file_stats in stats['file_stats'].items():
        if file_stats['retried'] > 0:
            print(f"{filename}:")
            print(f"  Failed lines found: {file_stats['failed_lines']}")
            print(f"  Retried: {file_stats['retried']}")
            print(f"  Success: {file_stats['success']}")
            print(f"  Still failed: {file_stats['still_failed']}")
            if file_stats['retried'] > 0:
                file_success_rate = (file_stats['success'] / file_stats['retried']) * 100
                print(f"  Success rate: {file_success_rate:.2f}%")
    
    print("=" * 60)


def main():
    """
    Main entry point for the retry script
    """
    parser = argparse.ArgumentParser(
        description="Retry decoding failed Google News URLs from decoded files"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="lunar_2026_data",
        help="Input directory containing *_decoded.txt files (default: lunar_2026_data)"
    )
    parser.add_argument(
        "--no-enhanced",
        action="store_true",
        help="Disable enhanced parsing method (use standard methods only)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backup files before updating"
    )
    
    args = parser.parse_args()
    
    # Determine input directory (relative to script location or absolute)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if os.path.isabs(args.input_dir):
        input_dir = args.input_dir
    else:
        input_dir = os.path.join(project_root, args.input_dir)
    
    print("=" * 60)
    print("Google News URL Retry Decoder")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Enhanced parsing: {not args.no_enhanced}")
    print(f"Create backups: {not args.no_backup}")
    print("=" * 60)
    
    # Process directory
    stats = process_directory(
        input_dir=input_dir,
        use_enhanced=not args.no_enhanced,
        backup=not args.no_backup
    )
    
    # Print summary
    if stats:
        print_summary(stats)
    else:
        print("No files were processed.")


if __name__ == "__main__":
    main()

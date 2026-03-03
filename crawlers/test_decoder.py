"""
Test script for Google News URL decoder
Helps diagnose decoding issues
"""

import sys
import os

# Add crawlers directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.google_news_decoder import decode_google_news_url, HAS_DECODER

def test_decoder():
    """Test the decoder with a sample URL"""
    print("=" * 60)
    print("Google News URL Decoder Test")
    print("=" * 60)
    
    # Check if googlenewsdecoder is available
    print(f"googlenewsdecoder available: {HAS_DECODER}")
    if not HAS_DECODER:
        print("Warning: googlenewsdecoder not installed. Install with: pip install googlenewsdecoder")
        print("Will use requests fallback method instead.")
    print()
    
    # Test URL from the actual data
    test_url = "https://news.google.com/rss/articles/CBMiWkFVX3lxTE5QUjlpamtrT0VFa1QzMmVTanM0ektfOU5GVVNNZFZKc3MyS0NVS0x1eFFEVW43Q3BKU01YMDBKNzdDVHN3ZWIxTjd0akhubVR2OW5CMEMwbHF1QQ?oc=5"
    
    print(f"Test URL: {test_url}")
    print("-" * 60)
    
    # Try decoding
    result = decode_google_news_url(test_url, use_fallback=True)
    
    print(f"Success: {result['success']}")
    print(f"Method: {result['method']}")
    print(f"Error: {result['error']}")
    print(f"Decoded URL: {result['decoded_url']}")
    print("=" * 60)
    
    if result['success']:
        print("✓ Decoding successful!")
    else:
        print("✗ Decoding failed!")
        print("\nTroubleshooting:")
        print("1. Make sure you have installed required packages:")
        print("   pip install googlenewsdecoder requests beautifulsoup4 lxml")
        print("2. Check your internet connection (requests method needs network)")
        print("3. Check if the URL format is correct")
    
    return result['success']

if __name__ == "__main__":
    success = test_decoder()
    sys.exit(0 if success else 1)

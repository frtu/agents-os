#!/usr/bin/env python3
"""
Downloader - URL to Markdown Converter

A simple tool to download web content and convert it to markdown format.
"""

import sys
import asyncio
import argparse

try:
    from .url_downloader import download_url_to_markdown
except ImportError:
    from url_downloader import download_url_to_markdown


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Downloader - URL to Markdown Converter with area organization",
        epilog="""
Examples:
  downloader https://example.com                                    # Basic download
  downloader https://docs.python.org/3/ -a python-docs            # Custom area
  downloader https://blog.example.com -a blog -r                   # Download with resources
  downloader https://tutorial.com -a tutorials --download-resources # Long form
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("url", help="URL to download")
    parser.add_argument(
        "-a", "--area",
        default="weekend-activities",
        help="Area folder name (default: weekend-activities)"
    )
    parser.add_argument(
        "-r", "--download-resources",
        action="store_true",
        default=False,
        help="Download images and videos (default: false)"
    )

    args = parser.parse_args()

    try:
        print(f"🌐 Downloading and converting: {args.url}")
        print(f"📂 Area: {args.area}")
        print(f"📦 Download resources: {args.download_resources}")

        filepath = asyncio.run(download_url_to_markdown(
            args.url,
            args.area,
            args.download_resources
        ))
        print(f"\n✅ Success! File saved to: {filepath}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

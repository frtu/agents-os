#!/usr/bin/env python3
"""
URL Downloader Script

Downloads content from a URL using Playwright and converts it to markdown format.
"""

import argparse
import asyncio
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

from markdownify import markdownify
from playwright.async_api import async_playwright


def sanitize_filename(text: str) -> str:
    """Sanitize a string to be used as a filename."""
    # Remove or replace invalid characters
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    # Remove extra whitespace and replace with underscores
    text = re.sub(r'\s+', '_', text)
    # Remove leading/trailing underscores and dots
    text = text.strip('_.')
    # Limit length
    return text[:100] if len(text) > 100 else text


def extract_base_url(url: str) -> str:
    """Extract base URL for folder naming."""
    parsed = urlparse(url)
    # Remove www. prefix if present
    domain = parsed.netloc.lower()
    if domain.startswith('www.'):
        domain = domain[4:]
    return sanitize_filename(domain)


async def download_media(page, media_urls: list, media_dir: Path, base_url: str) -> dict:
    """Download media files and return mapping of original URLs to local paths."""
    media_mapping = {}

    if not media_urls:
        return media_mapping

    print(f"📁 Creating media directory: {media_dir}")
    media_dir.mkdir(parents=True, exist_ok=True)

    for i, media_url in enumerate(media_urls):
        try:
            # Convert relative URLs to absolute
            if media_url.startswith('//'):
                media_url = 'https:' + media_url
            elif media_url.startswith('/'):
                media_url = urljoin(base_url, media_url)
            elif not media_url.startswith(('http://', 'https://')):
                media_url = urljoin(base_url, media_url)

            # Get file extension from URL
            parsed_media = urlparse(media_url)
            path_parts = parsed_media.path.split('/')
            filename = path_parts[-1] if path_parts[-1] else f"media_{i}"

            # Ensure filename has extension
            if '.' not in filename:
                # Try to determine from URL or default
                if any(ext in media_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        if ext in media_url.lower():
                            filename += ext
                            break
                elif any(ext in media_url.lower() for ext in ['.mp4', '.webm', '.mov', '.avi']):
                    for ext in ['.mp4', '.webm', '.mov', '.avi']:
                        if ext in media_url.lower():
                            filename += ext
                            break
                else:
                    filename += '.unknown'

            # Sanitize filename
            filename = sanitize_filename(filename)
            local_path = media_dir / filename

            # Handle duplicates
            counter = 1
            original_filename = filename
            while local_path.exists():
                name, ext = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, '')
                filename = f"{name}_{counter}.{ext}" if ext else f"{name}_{counter}"
                local_path = media_dir / filename
                counter += 1

            print(f"📥 Downloading: {media_url}")

            # Use Playwright to download the media
            response = await page.request.get(media_url)
            if response.status == 200:
                with open(local_path, 'wb') as f:
                    f.write(await response.body())
                # Store relative path from markdown file perspective
                media_folder_name = media_dir.name
                relative_path = f"./{media_folder_name}/{local_path.name}"
                media_mapping[media_url] = relative_path
                print(f"✅ Downloaded: {filename}")
            else:
                print(f"⚠️ Failed to download {media_url}: HTTP {response.status}")

        except Exception as e:
            print(f"⚠️ Failed to download {media_url}: {str(e)}")

    return media_mapping


async def download_url_to_markdown(url: str, area: str = "weekend-activities", download_resources: bool = False) -> str:
    """
    Download content from a URL and convert it to markdown.

    Args:
        url: The URL to download
        area: Area folder name
        download_resources: Whether to download media files

    Returns:
        Path to the saved markdown file
    """
    print(f"🌐 Downloading content from: {url}")
    print(f"📂 Area: {area}")
    print(f"📦 Download resources: {download_resources}")

    # Extract base URL and create directory structure
    base_url_folder = extract_base_url(url)

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to the URL
            response = await page.goto(url, wait_until="networkidle")

            if response and not response.ok:
                raise Exception(f"HTTP {response.status}: {response.status_text}")

            # Wait for content to load
            await page.wait_for_load_state("networkidle")

            # Get page title for filename
            title = await page.title()
            if not title:
                parsed_url = urlparse(url)
                title = f"{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}"

            # Get the HTML content
            html_content = await page.content()

            # Extract main content (try to get the body or main content)
            try:
                # Try to get just the main content area
                main_content = await page.locator("main, article, .content, #content, .post, .article").first.inner_html()
                if not main_content:
                    # Fallback to body content
                    main_content = await page.locator("body").inner_html()
            except:
                # If all else fails, use the full page content
                main_content = html_content

            media_urls = []
            media_mapping = {}

            if download_resources:
                # Extract media URLs
                print("🔍 Extracting media URLs...")

                # Get all images
                images = await page.locator("img").all()
                for img in images:
                    src = await img.get_attribute("src")
                    if src:
                        media_urls.append(src)

                # Get all videos
                videos = await page.locator("video").all()
                for video in videos:
                    src = await video.get_attribute("src")
                    if src:
                        media_urls.append(src)
                    # Also check for source tags within video
                    sources = await video.locator("source").all()
                    for source in sources:
                        src = await source.get_attribute("src")
                        if src:
                            media_urls.append(src)

                print(f"📊 Found {len(media_urls)} media files")

        except Exception as e:
            raise Exception(f"Failed to download content: {str(e)}")

        # Create directory structure
        safe_title = sanitize_filename(title)
        output_dir = Path("downloads") / area / base_url_folder
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate markdown filename
        filename = f"{safe_title}.md"
        filepath = output_dir / filename

        # Handle duplicate filenames
        counter = 1
        base_filename = safe_title
        while filepath.exists():
            filename = f"{base_filename}_{counter}.md"
            filepath = output_dir / filename
            counter += 1

        # Download media if requested
        if download_resources and media_urls:
            media_dir = output_dir / safe_title.replace('_', '-')
            media_mapping = await download_media(page, media_urls, media_dir, url)

        await browser.close()

    # Convert HTML to markdown
    print("📝 Converting HTML to markdown...")
    markdown_content = markdownify(
        main_content,
        heading_style="ATX",  # Use # style headers
        bullets="-",          # Use - for bullet points
        strip=["script", "style"]  # Remove script and style tags
    )

    # Update media references in markdown if we downloaded resources
    if media_mapping:
        print("🔗 Updating media references in markdown...")
        for original_url, local_path in media_mapping.items():
            # Replace absolute URLs with relative paths
            markdown_content = markdown_content.replace(original_url, local_path)
            # Also try to replace without protocol
            if original_url.startswith('//'):
                markdown_content = markdown_content.replace(original_url, local_path)

    # Add metadata header
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"""---
title: {title}
source: {url}
area: {area}
downloaded: {timestamp}
resources_downloaded: {download_resources}
media_count: {len(media_urls) if download_resources else 0}
---

"""

    # Combine header and content
    full_content = header + markdown_content

    # Save to file
    print(f"💾 Saving to: {filepath}")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"✅ Successfully downloaded and converted: {filepath}")
    if media_mapping:
        print(f"📁 Downloaded {len(media_mapping)} media files")

    return str(filepath)


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download URL content and convert to markdown with area-based organization"
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
        # Run the async function
        filepath = asyncio.run(download_url_to_markdown(
            args.url,
            args.area,
            args.download_resources
        ))
        print(f"\n✅ File saved to: {filepath}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
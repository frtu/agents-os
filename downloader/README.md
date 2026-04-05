# Downloader - URL to Markdown Converter

A Python tool that downloads web content and converts it to clean markdown format using Playwright for web scraping and markdownify for conversion.

## Features

- 🌐 Downloads any web page content
- 📝 Converts HTML to clean markdown
- 🎭 Uses Playwright for reliable content extraction
- 📄 Adds metadata headers (title, source URL, timestamp)
- 🔄 Smart filename sanitization
- 📁 Configurable output directory with area organization
- 🎨 Area-based folder structure: ./{area}/{base-url}/
- 📦 Optional media download (images and videos)
- 🔗 Updates markdown links to reference downloaded media
- 🚫 Removes scripts, styles, and unwanted elements

## Quick Start

### Install as Global Tool (Recommended)
```bash
# Clone and install
git clone <repo-url> downloader
cd downloader
uv tool install .

# Use anywhere
downloader https://example.com
downloader https://docs.python.org/3/ -a python-docs
downloader https://blog.example.com -a blog -r  # Download with media
```

### Development Setup
```bash
# Clone repository
git clone <repo-url> downloader
cd downloader

# Install dependencies and browsers
uv sync
uv run playwright install

# Run directly
./downloader.sh https://example.com
```

## Usage Examples

### Basic Usage
```bash
# Download with default area "weekend-activities"
downloader https://example.com

# Custom area
downloader https://github.com/microsoft/playwright -a github-docs

# Download with media resources
downloader https://blog.example.com/post/123 -a blog --download-resources

# Short form
url-to-md https://tutorial.com -a tutorials -r
```

### Directory Structure Created
```
./downloads/{theme}/{base-url}/{filename}.md
./downloads/{theme}/{base-url}/{filename}/     # (if -r/--download-resources)
    image1.jpg
    image2.png
    video1.mp4
```

### Advanced Examples
```bash
# Download documentation with resources
downloader https://docs.python.org/3/tutorial/ -t python-docs -r

# Download blog posts to organized folders
downloader https://blog.example.com/post/123 -t blog-posts

# Multiple downloads with themes
for url in "https://site1.com" "https://site2.com"; do
  downloader "$url" -t research-sites
done
```

## Output Format

Each downloaded file includes enhanced metadata:

```markdown
---
title: Page Title
source: https://example.com
theme: weekend-activities
downloaded: 2026-04-04 09:33:42
resources_downloaded: true
media_count: 5
---

# Page Content

Clean markdown content with proper formatting...

![Downloaded Image](./page-title/image1.jpg)
```

## CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `url` | - | Required | URL to download |
| `--theme` | `-t` | `weekend-activities` | Theme folder name |
| `--download-resources` | `-r` | `false` | Download images and videos |

## Installation Methods

| Method | Command | Usage |
|--------|---------|-------|
| **Global Tool** | `uv tool install .` | `downloader <url> -t theme` |
| **Local Project** | `uv pip install -e .` | `uv run downloader <url>` |
| **Shell Scripts** | `chmod +x *.sh` | `./downloader.sh <url>` |
| **Direct Run** | None | `uv run python downloader/main.py <url>` |

See [PACKAGING.md](PACKAGING.md) for detailed packaging information.

## Requirements

- Python 3.13+
- uv package manager
- Playwright (auto-installed with browsers)

## Dependencies

- **playwright**: Web browser automation
- **markdownify**: HTML to Markdown conversion
- **beautifulsoup4**: HTML parsing (via markdownify)

## Project Structure

```
downloader/
├── downloader/              # Main package
│   ├── main.py             # Enhanced CLI interface
│   └── url_downloader.py   # Core functionality with media support
├── downloader.sh           # Shell wrapper
├── url-to-md.sh           # Alternative wrapper
├── pyproject.toml         # Package configuration
└── README.md
```

## New Features

### Theme-Based Organization
- Files saved to `./downloads/{theme}/{base-url}/{filename}.md`
- Automatic base URL extraction and sanitization
- Customizable themes for different projects

### Media Download
- Downloads images (jpg, png, gif, webp) and videos (mp4, webm, mov)
- Creates organized media folders: `./downloads/{theme}/{base-url}/{filename}/`
- Updates markdown links to reference local files
- Smart filename handling and deduplication

## Examples

```bash
# Weekend activities research
downloader https://timeout.com/singapore/things-to-do-this-weekend

# Python documentation
downloader https://docs.python.org/3/tutorial/ -t python-docs -r

# Blog with media
downloader https://css-tricks.com/article-title -t web-dev --download-resources
```

Results in:
```
downloads/weekend-activities/timeout.com/Best_Things_To_Do_This_Weekend.md
downloads/python-docs/docs.python.org/Python_Tutorial.md
downloads/python-docs/docs.python.org/Python_Tutorial/
    diagram1.png
    example.py
downloads/web-dev/css-tricks.com/Article_Title.md
downloads/web-dev/css-tricks.com/Article_Title/
    screenshot1.jpg
    demo.gif
```

## License

[Add your license here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit a pull request

---

**Generated with uv and Playwright** 🎭
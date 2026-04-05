#!/bin/bash
# URL to Markdown converter wrapper script
# Usage: ./url-to-md.sh <url> [-a area] [-r]
#
# Examples:
#   ./url-to-md.sh https://example.com
#   ./url-to-md.sh https://docs.python.org/3/ -a python-docs
#   ./url-to-md.sh https://blog.example.com -a blog -r

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the url-to-md using the installed console script
exec uv run url-to-md "$@"
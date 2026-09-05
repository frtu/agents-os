#!/bin/bash

# file-rename-kebab-case: Rename files to lowercase kebab-case
# - Converts filename to lowercase
# - Replaces spaces and special characters with hyphens
# - Collapses repeated hyphens and trims leading/trailing hyphens
# - Skips .DS_Store and README.md files
# - Preserves the file extension
#
# Usage: file-rename-kebab-case.sh <folder>

target="$1"

if [[ -z "$target" ]]; then
    echo "Error: missing folder argument." >&2
    echo "Usage: $0 <folder>" >&2
    exit 1
fi

if [[ ! -d "$target" ]]; then
    echo "Error: '$target' is not a directory." >&2
    exit 1
fi

find "$target" -type f ! -name ".DS_Store" ! -name "README.md" ! -path "*/.git/*" | sort | while read file; do
    dir=$(dirname "$file")
    filename=$(basename "$file")

    # Separate extension from filename
    if [[ "$filename" == *.* ]]; then
        extension=".${filename##*.}"
        name="${filename%.*}"
    else
        extension=""
        name="$filename"
    fi

    # Transform: lowercase, replace any run of non-alphanumeric chars with a single
    # hyphen, then strip leading/trailing hyphens
    newname=$(echo "$name" | \
        tr '[:upper:]' '[:lower:]' | \
        sed -E 's/[^a-z0-9]+/-/g' | \
        sed -E 's/^-+//; s/-+$//')

    newfile="$dir/$newname$extension"

    # Only rename if different
    if [[ "$file" != "$newfile" ]]; then
        echo "Renaming: $file → $newfile"
        mv "$file" "$newfile"
    fi
done

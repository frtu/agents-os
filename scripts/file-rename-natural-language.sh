#!/bin/bash

# file-rename-natural-language: Rename files to Title Case with spaces between words
# - Replaces hyphens/underscores with spaces
# - Replaces special characters with underscores
# - Capitalizes first letter of each word
# - Skips .DS_Store and README.md files
# - Uses git mv to preserve history

find . -type f ! -name ".DS_Store" ! -name "README.md" ! -path "./.git/*" | sort | while read file; do
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

    # Transform: replace hyphens/underscores with spaces, replace special chars with underscore
    # Then convert to Title Case (capitalize each word)
    newname=$(echo "$name" | \
        sed 's/[-_]/ /g' | \
        sed 's/[^a-zA-Z0-9 ]/_/g' | \
        awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2); print}')

    newfile="$dir/$newname$extension"

    # Only rename if different
    if [[ "$file" != "$newfile" ]]; then
        echo "Renaming: $file → $newfile"
        mv "$file" "$newfile"
    fi
done

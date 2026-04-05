# Downloader Business Specifications

## Overview

The Downloader is a content archival system that captures web pages and converts them into organized, searchable markdown files. It provides systematic organization through theme-based categorization and preserves multimedia resources for offline access.

## Core Business Functions

### Content Capture
- **Web Page Retrieval**: Captures complete web page content from any accessible URL
- **Content Extraction**: Isolates main content from navigation, advertisements, and extraneous elements
- **Format Conversion**: Transforms HTML content into clean, readable markdown format
- **Metadata Enrichment**: Adds structured metadata for cataloging and searchability

### Content Organization
- **Theme-based Classification**: Groups content by project, topic, or research area
- **Domain-based Grouping**: Organizes content by source website for easy reference
- **Hierarchical Storage**: Creates logical folder structures for intuitive browsing

### Resource Management
- **Media Preservation**: Downloads and locally stores images, videos, and multimedia content
- **Link Maintenance**: Updates content references to point to locally stored media
- **File Organization**: Creates dedicated folders for multimedia assets

## Directory Structure & Organization

### Primary Structure
```
./downloads/{theme}/{domain}/{content-file}.md
```

### Components

**Downloads Root** (`./downloads/`)
- Central repository for all captured content
- Ensures clean separation from system and project files
- Provides single location for backup and maintenance

**Theme Level** (`{theme}/`)
- Primary organizational category (default: "weekend-activities")
- Examples: research, documentation, tutorials, references
- User-defined for project flexibility

**Domain Level** (`{domain}/`)
- Website source organization (e.g., "docs.python.org", "github.com")
- Removes "www." prefix for standardization
- Sanitized for filesystem compatibility

**Content File** (`{content-file}.md`)
- Individual page content in markdown format
- Filename derived from page title or URL structure
- Sanitized for cross-platform compatibility

### Media Resource Organization
When media downloading is enabled:
```
./downloads/{theme}/{domain}/{content-file}/
    ├── image1.jpg
    ├── image2.png
    ├── video1.mp4
    └── document1.pdf
```

**Media Folder Rules**:
- Created alongside markdown file when resources are downloaded
- Named after the main content file for association
- Contains all multimedia assets referenced in the content
- Preserves original file types and formats

## Metadata Schema

Each markdown file includes a YAML frontmatter header with structured metadata:

```yaml
---
title: [Page Title]
source: [Original URL]
theme: [Theme Category]
downloaded: [Timestamp: YYYY-MM-DD HH:MM:SS]
resources_downloaded: [true/false]
media_count: [Number of media files]
---
```

### Metadata Fields

**Title**
- Original page title from HTML `<title>` tag
- Fallback to domain + path if title unavailable
- Used for content identification and search

**Source**
- Complete original URL for reference and verification
- Enables re-downloading or update checking
- Maintains provenance chain

**Theme**
- User-specified categorization tag
- Enables content grouping and project organization
- Supports filtering and batch operations

**Downloaded**
- Capture timestamp for version tracking
- Enables freshness assessment
- Supports content lifecycle management

**Resources Downloaded**
- Boolean flag indicating media capture status
- Helps users understand content completeness
- Guides offline access expectations

**Media Count**
- Quantifies multimedia assets captured
- Assists in storage planning
- Provides content richness indicator

## Content Processing Rules

### Title Processing
1. Extract HTML title tag content
2. If unavailable, construct from domain + URL path
3. Sanitize for filesystem compatibility
4. Truncate to reasonable length (100 characters)
5. Handle duplicate titles with numerical suffixes

### Domain Processing
1. Extract domain from URL
2. Remove protocol (http/https)
3. Remove "www." prefix for standardization
4. Sanitize special characters
5. Convert to lowercase for consistency

### Content Extraction
1. Prioritize main content areas (article, main, .content)
2. Fall back to body content if main areas unavailable
3. Remove script, style, and navigation elements
4. Preserve semantic structure and formatting
5. Maintain internal link references

## Theme-Based Organization

### Theme Purpose
- **Project Separation**: Isolate different research or work streams
- **Content Categorization**: Group related materials logically
- **Access Control**: Enable theme-specific permissions or sharing
- **Lifecycle Management**: Apply retention policies by theme

### Theme Naming
- User-defined string (default: "weekend-activities")
- Filesystem-safe characters only
- Descriptive and consistent within organization
- Examples: research, documentation, tutorials, references

### Theme Benefits
- **Scalability**: Handle multiple projects without content mixing
- **Organization**: Logical grouping reduces search time
- **Sharing**: Enable selective content sharing by theme
- **Maintenance**: Targeted cleanup and archival operations

## Media Resource Management

### Media Detection
- **Images**: JPG, PNG, GIF, WEBP, SVG formats
- **Videos**: MP4, WEBM, MOV, AVI formats
- **Audio**: MP3, WAV, OGG formats (if present)
- **Documents**: PDF, DOC files referenced as media

### Download Strategy
- **Selective**: Only when explicitly requested via flag
- **Comprehensive**: All detected media in content
- **URL Resolution**: Convert relative URLs to absolute
- **Error Resilient**: Continue on individual media failures

### Link Processing
- **Reference Updates**: Modify markdown to use local paths
- **Relative Paths**: Use "./{filename}" format for portability
- **Preservation**: Maintain original URL in comments
- **Verification**: Ensure downloaded media matches references

## File Naming Conventions

### Filename Generation
1. **Source**: Page title or URL-derived name
2. **Sanitization**: Remove invalid filesystem characters
3. **Length Limits**: Truncate to 100 characters maximum
4. **Uniqueness**: Add numerical suffixes for duplicates
5. **Extensions**: Always use .md for markdown files

### Character Handling
- **Invalid Characters**: `< > : " / \ | ? *` → replaced with `_`
- **Whitespace**: Multiple spaces → single underscore
- **Special Cases**: Leading/trailing dots and underscores removed
- **Unicode**: Preserved where filesystem supports

### Duplicate Resolution
- **Detection**: Check existing files before creation
- **Numbering**: Add `_1`, `_2`, `_3` suffixes
- **Preservation**: Never overwrite existing content
- **Consistency**: Apply same logic to media files

## Business Rules

### Content Capture Rules
1. **Accessibility**: Only capture publicly accessible content
2. **Completeness**: Capture full page state at time of access
3. **Integrity**: Preserve content structure and formatting
4. **Attribution**: Maintain source URL and timestamp

### Organization Rules
1. **Hierarchy**: Theme → Domain → Content structure must be maintained
2. **Consistency**: File naming and structure uniform across captures
3. **Isolation**: Themes must not interfere with each other
4. **Portability**: Structure must work across different file systems

### Media Rules
1. **User Choice**: Media download only when explicitly requested
2. **Association**: Media files must be linked to source content
3. **Formats**: Preserve original media formats when possible
4. **Fallback**: Graceful handling of media download failures

### Quality Rules
1. **Clean Output**: Remove advertisements and navigation elements
2. **Readable Format**: Ensure markdown is properly structured
3. **Complete Metadata**: All required metadata fields must be populated
4. **Valid Structure**: Directory structure must be valid and accessible

## Use Cases

### Research and Documentation
- **Academic Research**: Organize papers and references by topic
- **Product Documentation**: Archive technical documentation
- **Competitive Analysis**: Collect and categorize competitor materials
- **Reference Library**: Build searchable knowledge base

### Content Archival
- **Important Articles**: Preserve valuable content against link rot
- **Historical Records**: Capture time-sensitive information
- **Offline Access**: Enable content access without internet
- **Backup Strategy**: Create local copies of critical web resources

### Project Management
- **Resource Collection**: Gather materials for specific projects
- **Team Sharing**: Organize content for team access
- **Progress Tracking**: Document research progress over time
- **Knowledge Transfer**: Preserve institutional knowledge

## Success Metrics

### Content Quality
- **Readability**: Markdown renders correctly across viewers
- **Completeness**: All intended content captured successfully
- **Accuracy**: Content matches original source faithfully
- **Usability**: Content is searchable and navigable

### Organization Effectiveness
- **Discoverability**: Users can locate content efficiently
- **Scalability**: System handles growing content volume
- **Maintenance**: Structure supports easy content management
- **Portability**: Content can be moved or shared effectively

### User Experience
- **Simplicity**: Basic usage requires minimal learning
- **Flexibility**: Advanced features available when needed
- **Reliability**: Consistent results across different websites
- **Performance**: Reasonable capture times for typical content
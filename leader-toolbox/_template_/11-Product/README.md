# 11-Product Folder Structure

## Purpose

This folder contains long term product-related information, including vision documents, analysis, processes, and storage solutions.

Note : Usually a product is NOT time bounded and continue to aggregate infos.

## Structure Pattern
```
11-Product/
├── README.md                               # This file
├── _Vision-[Product Name]_.md              # Vision and strategy documents
├── _Vision-[Product Name]_/                # Vision and strategy resources (PDF, images, ...)
├── [Product Area].md                       # Product area summary file
├── [Product Area]/                         # Product area resources
├── [Product Area]/[Feature theme].md       # A group / cluster of features solving a specific development concerns organised by theme
```

## Content Guidelines

### Root Level Documents
- **Product area summaries** (e.g., `Event trigger.md`) - Overview of specific product areas
- **General product documents** - Cross-cutting product concerns and vision
- **Company level documents** - Broader organizational challenges and context

### Specialized Subfolders

#### `_Vision-Workflow_`

- Strategic documents and vision statements
- High-level product direction and roadmaps
- Enclosed in double underscores for emphasis

#### `Trigger`

For each product area, create a dedicated `Trigger.md` file and a subfolder `Trigger/` :

- `Triggers/Event Trigger.md`: a group / cluster of features solving a specific development concerns organised by theme. Inside this file, all features are organised under `# Features` each having a H2 headers `## <feature_name>`. On the top of this document create a overview in less than 200 words `# Overview`.

### Current Structure Example
```
10-Product/
├── _Vision-Workflow_.md                # Vision doc
├── _Vision-Workflow_/                  # Strategic documents
├── Triggers.md                         # Triggers overview
├── Triggers/                           # Triggers content
├── Triggers/Event Trigger.md           # Event Trigger content
```

## AI Generation Instructions

To recreate this exact structure:

1. **Create main product area folders**:
   - Use simple, descriptive names (`Event trigger`, `Time trigger`, `Manual`)
   - Create `_Vision_` file & folder with single underscores for strategic content

2. **Create summary files** for each major product area:
   - Name pattern: `[Product Area].md` (e.g., `Triggers.md`)
   - Place in root directory as overview/entry point

3. **Organize by product domain**, not by document type:
   - Group related content in domain-specific folders
   - Keep cross-cutting documents at root level

4. **Use descriptive naming** for documents that reflects their content and scope

5. **Maintain separation** between strategic vision documents (`_Vision_/`) and operational content
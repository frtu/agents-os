# 1-Team Folder Structure

## Purpose
This folder contains team-related information, including team member profiles, hiring documents, and team enablement materials.

## Structure Pattern
```
1-Team/
├── README.md                     # This file
├── People - [Name]/             # Individual team member folders
│   └── [related files]         # Member-specific documents
└── People - [Name].md           # Individual team member profiles
```

## Content Guidelines

### People Folders Pattern
- **Folder Name**: `People - [First Name]`
- **Profile File**: `People - [First Name].md` (in root)
- **Supporting Documents**: Stored in respective person's subfolder

### Current Structure Example
```
1-Team/
├── People - Fred/             # Individual folder
├── People - Fred.md           # Profile file
├── People - Tony/             # Individual folder
├── People - Tony.md           # Profile file
```

## AI Generation Instructions

To recreate this exact structure:

1. **Create root team documents** with descriptive names ending in `.md`
2. **For each team member**:
   - Create a folder named `People - [First Name]`
   - Create a profile file named `People - [First Name].md` in the root directory
   - Place member-specific documents in their respective subfolder
3. **Maintain naming consistency** with "People - " prefix for all individual folders and files
4. **Keep general team documents** in the root of the 1-Team folder
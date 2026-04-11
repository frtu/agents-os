# 20-Projects Folder Structure

## Purpose

This folder contains project-specific documentation, including active projects, incident management, and individual project folders with supporting materials.

Note : Usually a project is time bounded with clear start and delivery time.

## Structure Pattern
```
20-Projects/
├── README.md                       # This file
├── [Project Name].md               # Project overview/summary files
├── [Project Name]/                 # Individual project folders
│   └── [project files]             # Project-specific documentation
├── _Incident_/                     # Special incident management folder
├── _Incident_/[Incident code].md   # Specific incident code name
```

## Content Guidelines

### Root Level Documents

- **Project summary files** (e.g., `Migration to Temporal.md`)
- **Project overviews** that correspond to project folders
- **Cross-project documentation** and general project information

### Special Folders

- **_Incident_/** - Incident management and response documentation (special naming with underscores)

### Project Folders

- **Individual project directories** with descriptive names
- **Supporting documentation** within each project folder
- **Consistent naming** between folder and summary file

### Document Types

- **Project summaries**: Overview documents for each major project
- **Technical documentation**: Implementation details and specifications
- **Project planning**: Timelines, requirements, and deliverables
- **Incident documentation**: Response procedures and post-mortems

### Current Structure Example

```
20-Projects/
├── Assistant/                               # Project folder
├── Assistant.md                             # Project summary
├── _Incident_/                              # Special incident folder
├── _Incident_/INC-123.md                    # Specific incident code description
```

## AI Generation Instructions

To recreate this exact structure:

1. **Create dual documentation approach**:
   - For major projects: both `[Project Name]/` folder AND `[Project Name].md` file
   - Summary file provides overview, folder contains detailed documentation

2. **Use descriptive project names**:
   - Clear, business-oriented naming (e.g., "Assistant")
   - Consistent naming between folders and summary files

3. **Special folder naming**:
   - Use `_Incident_/` with underscores for special operational folders
   - Keep standard project folders without special characters

4. **Organize by project lifecycle**:
   - Active projects get both folder and summary file
   - Smaller projects may only need summary files
   - Archive completed projects but maintain structure

5. **Maintain project independence**:
   - Each project folder is self-contained
   - Summary files provide entry points and overviews
   - Cross-project dependencies documented at root level
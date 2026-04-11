# 30-SOP-Runbooks

## Purpose
This folder contains Standard Operating Procedures (SOPs), operational guidelines, and process documentation for day-to-day operations.

## Structure Pattern
```
2-SOP/
├── README.md                     # This file
└── SOP-[Process Name].md         # Individual SOP documents
└── Runbook-[Process Name].md     # Individual Runbooks documents
```

## Content Guidelines

### Document Types
- **Operational procedures** for system management
- **Process documentation** for routine tasks
- **Requirements collection** procedures
- **Infrastructure request** processes

### Naming Convention
- Use descriptive names that clearly indicate the operational area
- Include the system or process being documented
- Keep names concise but specific

### Document Characteristics
- **Procedural content**: Step-by-step operational guides
- **Process templates**: Standardized approaches for common tasks
- **Requirements gathering**: Methods for collecting and documenting needs
- **Infrastructure management**: Operational procedures for system administration

### Current Structure Example
```
30-SOP-Runbooks/
├── SOP-Backup project.md                       # Step by step checklist to backup
├── SOP-Backup project/                         # Subfolder for ref resources (PDF and images)
├── Runbook-Troubleshoot OOM.md                 # Runbooks to troubleshoot how to deal with Out Of Memory (OOM)
```

## AI Generation Instructions

To recreate this exact structure:

1. **Keep flat structure** at root level:
   - All SOP documents directly in the 30-SOP-Runbooks folder
   - Subfolders for all related resources if exist

2. **Use descriptive naming** for procedures:
   - Include the system or technology (e.g., "PostgreSQL", "Kafka")
   - Describe the process clearly (e.g., "Requirements collection from Product A")
   - Use ".md" extension for all documents

3. **Focus on operational content**:
   - Document procedures, not concepts or architecture
   - Include step-by-step processes and guidelines
   - Maintain consistency in procedure format

4. **Organize by operational domain**:
   - Group related procedures logically
   - Consider the frequency and importance of procedures
   - Keep commonly used SOPs easily accessible

5. **Maintain procedural focus**:
   - Content should be actionable and process-oriented
   - Include templates, checklists, and step-by-step guides
   - Document both routine and exceptional procedures
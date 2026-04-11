# 2-Dependencies Folder Structure

## Purpose
This folder contains documentation about external dependencies, infrastructure requirements, and third-party system integrations that the Product relies on.

## Structure Pattern
```
2-Dependencies/
├── README.md                     # This file
└── [Dependency Name].md         # Individual dependency documents
```

## Content Guidelines

### Document Types
- **Infrastructure dependencies** (clusters, services, environments)
- **Third-party systems** and external service requirements
- **Cross-team dependencies** and shared resources
- **Environment-specific** configurations and requirements

### Naming Convention
- Use descriptive names that identify the specific dependency
- Include system type or technology when relevant
- Specify environment or context when applicable (e.g., "for Test environment")

### Content Focus
- **Dependency specifications** and requirements
- **Configuration details** for external systems
- **Integration points** with other teams or services
- **Access requirements** and permissions needed

### Current Structure Example
```
2-Dependencies/
└── Kafka for Test.md    # Sandbox cluster dependency for test
```

## AI Generation Instructions

To recreate this exact structure:

1. **Keep flat structure**:
   - All dependency documents at root level of 2-Dependencies folder
   
2. **Use descriptive naming**:
   - Include technology/system name (e.g., "Kafka")
   - Specify purpose or environment when relevant (e.g., "for test env")
   - Keep names clear and searchable

3. **Focus on external dependencies**:
   - Document systems and services outside direct control
   - Include infrastructure requirements and constraints
   - Specify integration requirements and access needs

4. **Maintain operational focus**:
   - Document what is needed, not how to implement
   - Include configuration requirements and specifications
   - Reference external systems and their requirements

5. **Scale with simplicity**:
   - Add more dependency documents as needed
   - Consider subfolders only when there are many related dependencies
   - Keep organization aligned with operational needs
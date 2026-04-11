---
Category: template
Kind:
  - 1-Intake
Tags:
  - project/active/search
Product:
  - "[[Search Overview]]"
Domain:
  - 
Project: "[[Project - TEMPLATE]]"
Parent: "[[Project - TEMPLATE]]"
Priority:
Effort:
Status:
Due: dd/mm/yyyy
Collaborators:
  - 
Ref link:
Doc link:
Description:
Last Updated: dd/mm/yyyy
---
(TEMPLATE) Search requirements & questions
# Functional Req

## Capabilities
- Ex : “Spend Activity” - Unified view & searchable across Entities/Categories
- **Filtering**
	- Ex : date, vendor/merchant, owner, department, etc
- **Permission model**
                
## Entities
- **Metadata**
	- **Source**
	- **Ownership**
	- **Lineage (Domain boundaries)**
- Ex : Bills
- Ex : Expenses
- Ex : Reimbursements
	- Ex : Procurements

## Relationship & Processing
- **Stateless (no joins)**
	- **Type conversion (1 input 1 output)**
	- **Filters (1 input 0 output)**
- **Enrichment (joins)?**
	
- **Mode & Freshness**
	- **Streaming**
	- **Batch**

## Storage
- **Dual Store**
	- **ElasticSearch?**
	- **Analytic - ClickHouse?**
		
- **Update Details**
	- **Mode**
		- **Full (erase & replace)?**
		- **Partial (incremental change)?**
	- **Origin**
		- **1 source of truth (simple)?**
		- **Many source to 1 (complex)?**
                    
# Non functional Req
- **Consistency & Race condition**
	- **Upsert**
	- **Version seq**
		- CDC LSN
		- Custom field
- **SLA**
	- **Availability (Uptime)**
	- **Performance & Latency**

# Solution Gap & Proposal
- **Tech design**
	- Ex : Only ingest to ES at the end
	- Ex : Pre compute everything

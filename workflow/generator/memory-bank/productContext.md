# Product Context: Workflow DAG generator

## Why This Project Exists

### Problem Statement
Organizations need to map internal work process into step by step operations & decisions in order to accomplish an action succesfully. It usually takes **multiple people/roles** to translate from a requester into a language executable by machine :

1. Requesters : customers or people representing & reformulating for them
* Reviewers : experts able to validate coherency, feasibility, etc
* Executors : running it operations as described

Suppose that Executors are handled by Workflow engines, **requesters to reviewers often requires multiple iterations**, review & testing before going live. When maintenance and evolution is required, when new group of people are involved, iterations has to **restart from zero and re-explain** some part of the problem in order to explain the new one.

If this could be delegate to a people to AI interaction, requester could 

* directly express, 
* understand and reformulate, 
* validate and approve


### Business Value
- **Fast TTM (time to market):** Quickly formulate and test application live providing immediate insights on experience
- **Quicker feedback loop:** Quickly test application live correct and retry
- **Avoid intermediate formulation :** Straight from needs to result

## Target Use Cases

### Primary Use Case: Internal process
- **Input:** Triggering events
- **Processing:** Steps to check and capture into systems
- **Output:** System of record capturing & aggregating different metrics
- **Users:** Domain expert selecting triggering events & defining process when event happens

## User Experience Goals

### Developer Experience

Workflow generator :

- **Quick definition:** Use english to define & visualise workflow
- **Local Testing:** Generate test data and quickly feed into the system
- **Easy Deployment:** Quickly push from test to prod

### Operations Experience

Workflow runtime :

- **Monitoring:** Clear events metrics and processing status
- **Fault Tolerance:** Detect undefined condition

## Solution Approach

### Key Features
1. **Event & Operation catalog**
   - Predefine all the event the user needs & available operations

2. **UI for conversation**
   - User is able to type in English his need
   - AI is able to reformulate what it understands & generate a mermaid graph

### Format

Eventually mermaid flowcharts could be used to represent workflow definition to requester.

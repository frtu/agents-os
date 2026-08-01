# Mermaid Architecture Patterns

Common patterns for architecture and integration diagrams.

## 1. Request-Response Flow

```mermaid
flowchart TD
    CLIENT([Client]) -->|request| API[API Gateway]
    API --> SERVICE[Service]
    SERVICE --> DB[(Database)]
    DB -->|data| SERVICE
    SERVICE -->|response| API
    API -->|response| CLIENT
```

## 2. Fan-Out Pattern (Multi-Source Query)

```mermaid
flowchart TD
    REQ([Request]) --> ORCH[Orchestrator]
    
    subgraph Sources["Data Sources"]
        S1[(Source 1)]
        S2[(Source 2)]
        S3[(Source 3)]
    end
    
    ORCH --> S1 & S2 & S3
    S1 & S2 & S3 --> AGG[Aggregator]
    AGG --> RESP([Response])
```

## 3. Pipeline Pattern

```mermaid
flowchart LR
    INPUT([Input]) --> STAGE1[Stage 1]
    STAGE1 --> STAGE2[Stage 2]
    STAGE2 --> STAGE3[Stage 3]
    STAGE3 --> OUTPUT([Output])
```

## 4. Layered Architecture

```mermaid
flowchart TD
    subgraph Presentation["Presentation Layer"]
        UI[Web UI]
        CLI[CLI]
    end
    
    subgraph Application["Application Layer"]
        API[API Service]
        AUTH[Auth Service]
    end
    
    subgraph Data["Data Layer"]
        DB[(Primary DB)]
        CACHE[(Cache)]
    end
    
    UI & CLI --> API
    API --> AUTH
    API --> DB
    API --> CACHE
```

## 5. Event-Driven Architecture

```mermaid
flowchart LR
    PRODUCER[Producer] -->|publish| QUEUE{{Message Queue}}
    QUEUE -->|consume| CONSUMER1[Consumer 1]
    QUEUE -->|consume| CONSUMER2[Consumer 2]
    CONSUMER1 --> DB1[(Store 1)]
    CONSUMER2 --> DB2[(Store 2)]
```

## 6. Security-Filtered Flow

```mermaid
flowchart TD
    REQ([Request]) --> AUTHN[AuthN]
    AUTHN -->|JWT| AUTHZ[AuthZ]
    AUTHZ -->|policy check| FILTER[Security Filter]
    FILTER -->|filtered query| SERVICE[Service]
    SERVICE --> RESP([Response])
    
    style AUTHN fill:#fff3e0
    style AUTHZ fill:#fff3e0
    style FILTER fill:#fff3e0
```

## 7. Sequence Diagram (Service Interaction)

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway
    participant S as Service
    participant D as Database
    
    C->>G: request
    G->>G: validate token
    G->>S: forward request
    S->>D: query
    D-->>S: results
    S-->>G: response
    G-->>C: response
```

## Shape Reference

| Shape | Syntax | Use For |
| --- | --- | --- |
| Rectangle | `[Name]` | Services, components |
| Rounded | `(Name)` | Processes |
| Stadium | `([Name])` | Start/end points |
| Cylinder | `[(Name)]` | Databases, stores |
| Diamond | `{Name}` | Decisions |
| Hexagon | `{{Name}}` | Queues, async |
| Parallelogram | `[/Name/]` | Input/output |

## Edge Labels

```mermaid
flowchart LR
    A -->|"labeled"| B
    C -.->|"dashed"| D
    E ==>|"thick"| F
```

## Styling

```mermaid
flowchart TD
    A[Normal]
    B[Highlighted]
    C[Warning]
    
    style A fill:#ffffff
    style B fill:#c8e6c9
    style C fill:#ffcdd2
```

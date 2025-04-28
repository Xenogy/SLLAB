# System Architecture Diagram

This diagram illustrates the high-level architecture of the AccountDB system.

```mermaid
graph TD
    subgraph "Frontend"
        UI[User Interface]
        FE_Logic[Frontend Logic]
    end

    subgraph "Backend API"
        API[API Endpoints]
        Auth[Authentication]
        Validation[Input Validation]
        ErrorHandling[Error Handling]
    end

    subgraph "Business Logic"
        Services[Services]
        Repositories[Repositories]
    end

    subgraph "Database"
        DB[PostgreSQL]
        RLS[Row-Level Security]
    end

    subgraph "Proxmox Integration"
        ProxmoxAgent[Proxmox Host Agent]
        ProxmoxAPI[Proxmox API Client]
    end

    UI --> FE_Logic
    FE_Logic --> API
    API --> Auth
    API --> Validation
    API --> ErrorHandling
    Auth --> Services
    Validation --> Services
    ErrorHandling --> Services
    Services --> Repositories
    Services --> ProxmoxAPI
    Repositories --> DB
    DB --> RLS
    ProxmoxAPI --> ProxmoxAgent
    ProxmoxAgent --> Proxmox[Proxmox Nodes]

    style UI fill:#f9f,stroke:#333,stroke-width:2px
    style DB fill:#bbf,stroke:#333,stroke-width:2px
    style Proxmox fill:#bfb,stroke:#333,stroke-width:2px
```

## Architecture Description

The AccountDB system follows a layered architecture with clear separation of concerns:

1. **Frontend Layer**: Provides the user interface and client-side logic for interacting with the backend API.
   
2. **Backend API Layer**: Handles HTTP requests, authentication, input validation, and error handling.
   
3. **Business Logic Layer**: Contains services that implement business rules and repositories that abstract database access.
   
4. **Database Layer**: PostgreSQL database with Row-Level Security (RLS) to ensure data isolation between users.
   
5. **Proxmox Integration Layer**: Connects to Proxmox nodes through a host agent and API client to manage VMs and containers.

This architecture promotes maintainability, scalability, and security by separating concerns and implementing proper access controls.

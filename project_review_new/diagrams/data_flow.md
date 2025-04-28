# Data Flow Diagram

This diagram illustrates the flow of data through the AccountDB system.

```mermaid
graph TD
    User[User] -->|Interacts with| UI[User Interface]
    UI -->|Sends requests to| API[API Endpoints]
    API -->|Authenticates| Auth[Authentication Service]
    Auth -->|Validates token| DB1[Database]
    API -->|Validates input| Validation[Input Validation]
    API -->|Processes requests| Services[Business Services]
    
    Services -->|Retrieves/stores data| Repositories[Data Repositories]
    Repositories -->|Executes queries with RLS| DB2[Database with RLS]
    
    Services -->|VM operations| ProxmoxClient[Proxmox API Client]
    ProxmoxClient -->|Communicates with| ProxmoxAgent[Proxmox Host Agent]
    ProxmoxAgent -->|Manages VMs on| ProxmoxNodes[Proxmox Nodes]
    
    ProxmoxNodes -->|VM status updates| ProxmoxAgent
    ProxmoxAgent -->|VM data| ProxmoxClient
    ProxmoxClient -->|Updates VM info| Services
    Services -->|Updates VM records| Repositories
    
    DB2 -->|Query results| Repositories
    Repositories -->|Data objects| Services
    Services -->|Response data| API
    API -->|Formatted response| UI
    UI -->|Displays information| User
    
    style User fill:#f96,stroke:#333,stroke-width:2px
    style UI fill:#f9f,stroke:#333,stroke-width:2px
    style DB2 fill:#bbf,stroke:#333,stroke-width:2px
    style ProxmoxNodes fill:#bfb,stroke:#333,stroke-width:2px
```

## Data Flow Description

The data flow in the AccountDB system follows these main paths:

### User Interaction Flow
1. User interacts with the User Interface
2. UI sends HTTP requests to API endpoints
3. API authenticates the request through the Authentication Service
4. Authentication Service validates the token against the database
5. API validates input data
6. API processes the request through Business Services
7. Services return response data to API
8. API formats and sends response to UI
9. UI displays information to the User

### Data Access Flow
1. Business Services request data from Data Repositories
2. Repositories execute queries against the database with Row-Level Security (RLS)
3. Database returns query results filtered by RLS policies
4. Repositories convert query results to data objects
5. Data objects are returned to Business Services

### Proxmox Integration Flow
1. Business Services send VM operation requests to Proxmox API Client
2. Proxmox API Client communicates with Proxmox Host Agent
3. Proxmox Host Agent manages VMs on Proxmox Nodes
4. Proxmox Nodes send VM status updates to Proxmox Host Agent
5. Proxmox Host Agent sends VM data to Proxmox API Client
6. Proxmox API Client updates VM information in Business Services
7. Business Services update VM records through Data Repositories

This data flow ensures proper separation of concerns, security through authentication and RLS, and integration with Proxmox for VM management.

# Component Diagram

This diagram illustrates the detailed components of the AccountDB system and their interactions.

```mermaid
graph TD
    subgraph "Frontend Components"
        Dashboard[Dashboard]
        AccountManagement[Account Management]
        HardwareManagement[Hardware Management]
        VMManagement[VM Management]
        ProxmoxNodeManagement[Proxmox Node Management]
        UserManagement[User Management]
    end

    subgraph "API Endpoints"
        AccountAPI[Account API]
        HardwareAPI[Hardware API]
        VMAPI[VM API]
        ProxmoxNodeAPI[Proxmox Node API]
        UserAPI[User API]
        AuthAPI[Auth API]
    end

    subgraph "Services"
        AccountService[Account Service]
        HardwareService[Hardware Service]
        VMService[VM Service]
        ProxmoxNodeService[Proxmox Node Service]
        UserService[User Service]
        AuthService[Auth Service]
    end

    subgraph "Repositories"
        AccountRepo[Account Repository]
        HardwareRepo[Hardware Repository]
        VMRepo[VM Repository]
        ProxmoxNodeRepo[Proxmox Node Repository]
        UserRepo[User Repository]
    end

    subgraph "Database Tables"
        AccountTable[Accounts]
        HardwareTable[Hardware]
        VMTable[VMs]
        ProxmoxNodeTable[Proxmox Nodes]
        UserTable[Users]
        WhitelistTable[Whitelist]
    end

    subgraph "Proxmox Integration"
        ProxmoxClient[Proxmox API Client]
        ProxmoxHostAgent[Proxmox Host Agent]
    end

    Dashboard --> AccountAPI
    Dashboard --> HardwareAPI
    Dashboard --> VMAPI
    Dashboard --> ProxmoxNodeAPI
    
    AccountManagement --> AccountAPI
    HardwareManagement --> HardwareAPI
    VMManagement --> VMAPI
    ProxmoxNodeManagement --> ProxmoxNodeAPI
    UserManagement --> UserAPI
    
    AccountAPI --> AccountService
    HardwareAPI --> HardwareService
    VMAPI --> VMService
    ProxmoxNodeAPI --> ProxmoxNodeService
    UserAPI --> UserService
    AuthAPI --> AuthService
    
    AccountService --> AccountRepo
    HardwareService --> HardwareRepo
    VMService --> VMRepo
    ProxmoxNodeService --> ProxmoxNodeRepo
    UserService --> UserRepo
    
    AccountRepo --> AccountTable
    HardwareRepo --> HardwareTable
    VMRepo --> VMTable
    ProxmoxNodeRepo --> ProxmoxNodeTable
    UserRepo --> UserTable
    VMService --> WhitelistTable
    
    VMService --> ProxmoxClient
    ProxmoxNodeService --> ProxmoxClient
    ProxmoxClient --> ProxmoxHostAgent
    
    style Dashboard fill:#f9f,stroke:#333,stroke-width:2px
    style AccountTable fill:#bbf,stroke:#333,stroke-width:2px
    style HardwareTable fill:#bbf,stroke:#333,stroke-width:2px
    style VMTable fill:#bbf,stroke:#333,stroke-width:2px
    style ProxmoxNodeTable fill:#bbf,stroke:#333,stroke-width:2px
    style UserTable fill:#bbf,stroke:#333,stroke-width:2px
    style WhitelistTable fill:#bbf,stroke:#333,stroke-width:2px
    style ProxmoxHostAgent fill:#bfb,stroke:#333,stroke-width:2px
```

## Component Description

The AccountDB system consists of the following key components:

### Frontend Components
- **Dashboard**: Main interface showing overview of accounts, hardware, VMs, and Proxmox nodes
- **Account Management**: Interface for managing accounts
- **Hardware Management**: Interface for managing hardware resources
- **VM Management**: Interface for managing virtual machines
- **Proxmox Node Management**: Interface for managing Proxmox nodes
- **User Management**: Interface for managing users and permissions

### API Endpoints
- **Account API**: Endpoints for account operations
- **Hardware API**: Endpoints for hardware operations
- **VM API**: Endpoints for VM operations
- **Proxmox Node API**: Endpoints for Proxmox node operations
- **User API**: Endpoints for user operations
- **Auth API**: Endpoints for authentication and authorization

### Services
- **Account Service**: Business logic for account operations
- **Hardware Service**: Business logic for hardware operations
- **VM Service**: Business logic for VM operations
- **Proxmox Node Service**: Business logic for Proxmox node operations
- **User Service**: Business logic for user operations
- **Auth Service**: Business logic for authentication and authorization

### Repositories
- **Account Repository**: Data access for accounts
- **Hardware Repository**: Data access for hardware
- **VM Repository**: Data access for VMs
- **Proxmox Node Repository**: Data access for Proxmox nodes
- **User Repository**: Data access for users

### Database Tables
- **Accounts**: Stores account information
- **Hardware**: Stores hardware information
- **VMs**: Stores VM information
- **Proxmox Nodes**: Stores Proxmox node information
- **Users**: Stores user information
- **Whitelist**: Stores whitelist information for VM access

### Proxmox Integration
- **Proxmox API Client**: Client for interacting with Proxmox API
- **Proxmox Host Agent**: Agent running on Proxmox nodes for direct interaction

# AccountDB

AccountDB is a comprehensive account management system designed to securely store and manage accounts with proper security controls and user separation. It provides a centralized platform for managing Steam accounts, virtual machines through Proxmox integration, and includes a Windows VM Agent for monitoring and automation.

## Features

### Core Features
- **Account Management**: Store and manage account credentials securely
- **User Management**: Role-based access control (admin, regular user)
- **Security**: Row-Level Security (RLS) to ensure users can only access their own data
- **API**: RESTful API for programmatic access
- **Frontend**: User-friendly web interface built with Next.js

### Advanced Features
- **Proxmox Integration**: Manage virtual machines through Proxmox
- **Windows VM Agent**: Monitor and automate actions on Windows VMs
- **Log Storage System**: Centralized logging with filtering and visualization
- **Performance Optimization**: Query optimization and caching
- **Monitoring**: Database performance monitoring and health checks
- **Reliability**: Automatic recovery from common database issues

## System Components

- **API Server**: FastAPI application providing RESTful endpoints
- **Database**: PostgreSQL database with Row-Level Security
- **Frontend**: Next.js web application
- **Log Storage System**: Centralized logging with UI for viewing and management
- **Proxmox Host Agent**: Agent for synchronizing VM information
- **Windows VM Agent**: Agent for monitoring and automation on Windows VMs

## Project Structure

- **backend/**: FastAPI application with API endpoints
- **frontend/**: Next.js web application
- **docs/**: Project documentation
- **scripts/**: Utility scripts for database management and testing
- **inits/**: Database initialization scripts
- **proxmox_host/**: Proxmox host agent for VM synchronization
- **windows_vm_agent/**: Agent for Windows VM monitoring and automation

## Getting Started

### Prerequisites

- Docker and Docker Compose
- PostgreSQL client (for running SQL scripts)
- Python 3.9+ (for running Python scripts)
- Proxmox VE (for VM management features)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/xenogy/sllab.git
   cd sllab
   ```

2. Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

3. Start the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost:8084
   - API: http://localhost:8080
   - API Documentation: http://localhost:8080/api/docs
   - Monitoring Dashboard: http://localhost:8080/monitoring

### Component Installation

#### Proxmox Host Agent
See [Proxmox Host Agent Documentation](proxmox_host/README.md) for installation instructions.

#### Windows VM Agent
See [Windows VM Agent Documentation](windows_vm_agent/README.md) for installation instructions.

## Documentation

For more detailed information, please refer to the [documentation](docs/README.md).

### Developer Documentation
- [Coding Standards](docs/developer_guides/coding_standards.md)
- [Contribution Guide](docs/developer_guides/contribution_guide.md)
- [Development Setup](docs/developer_guides/development_setup.md)
- [Testing Guide](docs/developer_guides/testing_guide.md)

### User Documentation
- [User Guide](docs/user_guides/user_guide.md)
- [Installation Guide](docs/user_guides/installation_guide.md)
- [Configuration Guide](docs/user_guides/configuration_guide.md)
- [Troubleshooting Guide](docs/user_guides/troubleshooting_guide.md)

### Architecture Documentation
- [Overview](docs/architecture/overview.md)
- [Database Schema](docs/database/schema.md)
- [Row-Level Security](docs/database/row_level_security.md)
- [API Architecture](docs/architecture/api_architecture.md)

## License

This project is proprietary and confidential.

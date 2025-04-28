# AccountDB

AccountDB is a comprehensive account management system designed to securely store and manage Steam accounts with proper security controls and user separation.

## Features

- **Account Management**: Store and manage account credentials securely
- **User Management**: Role-based access control (admin, regular user)
- **Security**: Row-Level Security (RLS) to ensure users can only access their own data
- **API**: RESTful API for programmatic access
- **Frontend**: User-friendly web interface
- **Performance**: Query optimization and caching for improved performance
- **Monitoring**: Database performance monitoring and health checks
- **Reliability**: Automatic recovery from common database issues

## Project Structure

- **backend/**: FastAPI application with API endpoints
- **frontend/**: Next.js web application
- **docs/**: Project documentation
- **scripts/**: Utility scripts for database management and testing
- **inits/**: Database initialization scripts
- **project_review/**: Project review documentation (historical reference)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- PostgreSQL client (for running SQL scripts)
- Python 3.8+ (for running Python scripts)

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
   - API Documentation: http://localhost:8080/docs
   - Monitoring Dashboard: http://localhost:8080/monitoring/health

## Documentation

For more detailed information, please refer to the [documentation](docs/README.md).

## License

This project is proprietary and confidential.

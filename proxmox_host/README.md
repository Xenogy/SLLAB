# Proxmox Host Agent for AccountDB

This agent runs on Proxmox host nodes and synchronizes VM information with the AccountDB server.

## Features

- Connects to the Proxmox API to gather VM information
- Processes and formats this information
- Sends it to the AccountDB API
- Runs on a schedule to keep the information up-to-date
- Provides a REST API for manual synchronization and status checks
- Sends logs to the central log storage system for monitoring and troubleshooting

## Installation

### Prerequisites

- Python 3.9 or higher
- Access to Proxmox API
- Access to AccountDB API

### Using Docker

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/accountdb.git
   cd accountdb/proxmox_host
   ```

2. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and run the Docker container:
   ```bash
   docker build -t proxmox-agent .
   docker run -d --name proxmox-agent -p 8000:8000 --env-file .env proxmox-agent
   ```

### Using Systemd Service

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/accountdb.git
   cd accountdb/proxmox_host
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Copy files to the installation directory:
   ```bash
   sudo mkdir -p /opt/proxmox-agent
   sudo cp -r * /opt/proxmox-agent/
   sudo cp .env /opt/proxmox-agent/
   ```

5. Install the systemd service:
   ```bash
   sudo cp proxmox-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable proxmox-agent
   sudo systemctl start proxmox-agent
   ```

## Configuration

The agent is configured using environment variables. You can set these in a `.env` file or directly in the environment.

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXMOX_HOST` | Proxmox API host URL | `https://proxmox.example.com:8006` |
| `PROXMOX_USER` | Proxmox API username (including realm, e.g., `root@pam`) | `root@pam` |
| `PROXMOX_PASSWORD` | Proxmox API password | - |
| `PROXMOX_VERIFY_SSL` | Whether to verify SSL certificates | `true` |
| `PROXMOX_NODE_NAME` | Proxmox node name | `pve` |
| `ACCOUNTDB_URL` | AccountDB API URL | `http://localhost:8080` |
| `ACCOUNTDB_API_KEY` | AccountDB API key | - |
| `ACCOUNTDB_NODE_ID` | Node ID in AccountDB | `1` |
| `UPDATE_INTERVAL` | Synchronization interval in seconds | `300` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORWARDING_ENABLED` | Enable log forwarding to central storage | `true` |
| `LOG_FORWARDING_LEVEL` | Minimum level for forwarded logs | `INFO` |
| `DEBUG` | Enable debug mode | `false` |

## API Endpoints

The agent provides the following API endpoints:

- `GET /health`: Health check endpoint
- `GET /sync/status`: Get synchronization status
- `POST /sync/trigger`: Trigger a manual synchronization
- `GET /vms`: Get all VMs from Proxmox
- `GET /vms/{vm_id}`: Get a specific VM from Proxmox
- `GET /config`: Get application configuration (excluding sensitive information)

## Monitoring

You can monitor the agent using the `/health` and `/sync/status` endpoints. The agent also logs information to stdout, which can be captured by Docker or systemd.

### Centralized Logging

The agent automatically sends logs to the central log system.

#### Configuration

Set these options in the `.env` file:

```
LOG_FORWARDING_ENABLED=true
LOG_FORWARDING_LEVEL=INFO
```

#### Viewing Logs

All logs can be viewed in the web interface at `/logs`. Filter by source (`proxmox_host`) to see only logs from this agent.

## How It Works

### VM Synchronization

The agent periodically fetches VM information from Proxmox and synchronizes it with the AccountDB backend. The synchronization process works as follows:

1. The agent connects to Proxmox using the credentials in the `.env` file
2. It retrieves the list of VMs from Proxmox
3. It filters the VMs based on the whitelist retrieved from AccountDB
4. It sends the filtered VM data to AccountDB
5. AccountDB updates its database with the VM information

### Owner ID

The agent automatically retrieves the owner ID from the AccountDB server during the connection verification process. This owner ID is used when creating new VMs in the database. You don't need to configure the owner ID manually.

## Troubleshooting

If you encounter issues, check the logs:

- Docker: `docker logs proxmox-agent`
- Systemd: `journalctl -u proxmox-agent`

Common issues:

- **Connection refused**: Check that the Proxmox API is accessible from the agent
- **Authentication failed**: Check your Proxmox API credentials
- **API key invalid**: Check your AccountDB API key
- **SSL verification failed**: Set `PROXMOX_VERIFY_SSL=false` if using self-signed certificates
- **Owner ID not found**: Make sure the Proxmox node is properly configured in AccountDB and has an owner assigned

## License

This project is licensed under the MIT License - see the LICENSE file for details.

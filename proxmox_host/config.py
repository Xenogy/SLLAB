"""
Configuration module for the Proxmox host agent.
"""

import os
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ProxmoxConfig(BaseModel):
    """Proxmox API configuration."""
    host: str
    user: str
    password: str
    verify_ssl: bool = True
    node_name: str

class AccountDBConfig(BaseModel):
    """AccountDB API configuration."""
    url: str
    api_key: str
    node_id: int

class LogConfig(BaseModel):
    """Log forwarding configuration."""
    enabled: bool = True
    level: str = "INFO"
    batch_size: int = 10
    flush_interval: int = 60  # seconds

class Config(BaseModel):
    """Application configuration."""
    proxmox: ProxmoxConfig
    accountdb: AccountDBConfig
    logging: LogConfig = LogConfig()
    update_interval: int = 300  # seconds
    log_level: str = "INFO"
    debug: bool = False

def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        proxmox=ProxmoxConfig(
            host=os.getenv("PROXMOX_HOST", "https://proxmox.example.com:8006"),
            user=os.getenv("PROXMOX_USER", "root@pam"),
            password=os.getenv("PROXMOX_PASSWORD", ""),
            verify_ssl=os.getenv("PROXMOX_VERIFY_SSL", "true").lower() == "true",
            node_name=os.getenv("PROXMOX_NODE_NAME", "pve"),
        ),
        accountdb=AccountDBConfig(
            url=os.getenv("ACCOUNTDB_URL", "http://localhost:8080"),
            api_key=os.getenv("ACCOUNTDB_API_KEY", "v8akQodLgRLDqMyE9-2hDyzCFvJCsSD7a1Ry3PxNPtk"),
            node_id=int(os.getenv("ACCOUNTDB_NODE_ID", "1")),
        ),
        logging=LogConfig(
            enabled=os.getenv("LOG_FORWARDING_ENABLED", "true").lower() == "true",
            level=os.getenv("LOG_FORWARDING_LEVEL", "INFO"),
            batch_size=int(os.getenv("LOG_BATCH_SIZE", "10")),
            flush_interval=int(os.getenv("LOG_FLUSH_INTERVAL", "60")),
        ),
        update_interval=int(os.getenv("UPDATE_INTERVAL", "300")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
    )

# Global configuration instance
config = load_config()

# AccountDB Documentation

This directory contains comprehensive documentation for the AccountDB project, a secure account management system with Proxmox integration and Windows VM agent capabilities.

## Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Database Documentation](#database-documentation)
- [API Documentation](#api-documentation)
- [Component Documentation](#component-documentation)
- [Developer Guides](#developer-guides)
- [User Guides](#user-guides)
- [Troubleshooting](#troubleshooting)

## Project Overview

- [Project Overview](project_overview.md): High-level overview of the project
- [Project Structure](project_structure.md): Detailed explanation of the project directory structure
- [System Components](architecture/overview.md): Description of system components and their interactions
- [Changes Summary](changes_summary.md): Summary of recent changes and improvements

## System Architecture

- [Architecture Overview](architecture/overview.md): Overall system architecture
- [Security Model](architecture/security_model.md): Security model and implementation
- [API Architecture](architecture/api_architecture.md): API architecture and endpoints
- [Frontend Architecture](architecture/frontend_architecture.md): Frontend architecture and components
- [Connection Management](architecture/connection_management.md): Database connection management
- [Credential Management](architecture/credential_management.md): Secure credential management
- [Input Validation](architecture/input_validation.md): Input validation approach

## Database Documentation

- [Database Schema](database/schema.md): Complete database schema documentation
- [Row-Level Security](database/row_level_security.md): Row-Level Security implementation
- [Normalized Database Schema](architecture/normalized_database_schema.md): Normalized database design
- [VMs Table](database/vms_table.md): Virtual machines table structure

## API Documentation

- [API Overview](api/README.md): Overview of the API endpoints
- [Authentication](architecture/security_model.md#authentication): API authentication
- [Authorization](architecture/security_model.md#authorization): API authorization
- [Error Handling](architecture/api_architecture.md#error-handling): API error handling

## Component Documentation

### Log Storage System

- [Log Storage System](log_storage.md): Centralized logging system documentation
- [Log Viewer](log_storage.md#log-viewer): Using the log viewer interface
- [Log Management](log_storage.md#log-management): Managing and cleaning up logs
- [Log Integration](log_storage.md#integration): Integrating with other components

### Proxmox Integration

- [Proxmox Host Agent](../proxmox_host/README.md): Documentation for the Proxmox host agent
- [VM Management](architecture/api_architecture.md#vm-management): VM management through the API

### Windows VM Agent

- [Windows VM Agent](../windows_vm_agent/README.md): Documentation for the Windows VM agent
- [Agent Configuration](../windows_vm_agent/README.md#configuration): Configuring the Windows VM agent
- [Event Monitoring](../windows_vm_agent/README.md#event-monitoring): Monitoring events with the agent
- [Action Scripts](../windows_vm_agent/README.md#creating-action-scripts): Creating action scripts for the agent

## Developer Guides

- [Coding Standards](developer_guides/coding_standards.md): Coding standards for the project
- [Contribution Guide](developer_guides/contribution_guide.md): Guide for contributing to the project
- [Development Setup](developer_guides/development_setup.md): Setting up the development environment
- [Testing Guide](developer_guides/testing_guide.md): Guide for testing the application

## User Guides

- [User Guide](user_guides/user_guide.md): General user guide
- [Installation Guide](user_guides/installation_guide.md): Installation instructions
- [Configuration Guide](user_guides/configuration_guide.md): Configuration options
- [Troubleshooting Guide](user_guides/troubleshooting_guide.md): Troubleshooting common issues

## Troubleshooting

- [Common Issues](user_guides/troubleshooting_guide.md): Common issues and their solutions
- [Database Issues](user_guides/troubleshooting_guide.md#database-issues): Troubleshooting database issues
- [API Issues](user_guides/troubleshooting_guide.md#api-issues): Troubleshooting API issues
- [Frontend Issues](user_guides/troubleshooting_guide.md#frontend-issues): Troubleshooting frontend issues
- [Proxmox Integration Issues](user_guides/troubleshooting_guide.md#proxmox-integration-issues): Troubleshooting Proxmox integration
- [Windows VM Agent Issues](user_guides/troubleshooting_guide.md#windows-vm-agent-issues): Troubleshooting Windows VM agent

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RunPod management and automation toolkit for working with RunPod cloud GPU instances. The project provides Python utilities for:
- Managing connections (SSH, S3 storage, API)
- File transfers between local machine and RunPod instances
- ComfyUI workflow setup and model management
- Disk space monitoring and cleanup
- Remote command execution

## Core Architecture

### Connection Management (`runpod_connections.py`)

The `RunPodConnections` class is the central component that handles all connection types:

**Credential Loading**:
- Reads from a `.env` file with flexible parsing
- Supports both `key=value` and `key: value` formats
- Normalizes credential keys (e.g., "AWS Access Key ID" → "aws_access_key_id")
- Extracts SSH connection details from ssh command strings

**Connection Types**:
1. **S3 Storage**: Boto3-based S3 client for RunPod's S3-compatible storage
2. **SSH/SFTP**: Paramiko-based SSH connections with automatic key discovery
3. **API**: GraphQL API client (currently less developed than S3/SSH)

**Key Design Patterns**:
- Lazy initialization: Clients created on first use
- Auto-reconnect: SSH methods attempt connection if not connected
- SSH key fallback: Searches multiple common key locations (~/.ssh/id_ed25519, id_rsa, etc.)
- Verbose mode for debugging connection issues

### File Transfer Layer (`file_transfer.py`)

Built on top of `RunPodConnections`, provides:
- Interactive CLI menu for file operations
- Command-line interface for scripting
- Directory upload with recursive structure preservation
- Both SSH and S3 transfer methods

### Configuration System

**Credentials File**: `.env`
- Contains S3 credentials (access key, secret, bucket, endpoint)
- Contains SSH connection strings that are parsed
- Format is flexible with aliases for common key names

**Connection Info Structure**:
```python
{
    'aws_access_key_id': str,
    'aws_secret_access_key': str,
    'bucket_name': str,
    'endpoint_url': str,
    'ssh_host': str,          # e.g., 'ssh.runpod.io'
    'ssh_username': str,       # e.g., 'im5qj03lqzxugv-64410c77'
    'ssh_port': int,          # default 22
    'ssh_ip': str             # optional direct IP
}
```

### ComfyUI Integration

**Model Management** (`download_workflow_models.py`):
- Defines model requirements for specific ComfyUI workflows
- Checks for existing models on RunPod before downloading
- Supports both interactive downloads and script generation
- Handles large model files (GGUF, FP8 formats)
- Model categories: diffusion_models, checkpoints, clip, vae, loras, clip_vision, model_patches

**Space Cleanup** (`cleanup_comfyui_space.py`):
- Dry-run mode by default (requires --execute flag)
- Removes temporary files (*.part, *.tmp, *_temp_*)
- Clears ComfyUI-Manager cache
- Reports incomplete downloads
- Analyzes output folder size

**Target Paths**:
- Base: `/workspace/ComfyUI`
- Models: `/workspace/ComfyUI/models/[category]/`
- Output: `/workspace/ComfyUI/output/`
- Cache: `/workspace/ComfyUI/user/default/ComfyUI-Manager/cache`

## Common Development Commands

### Setup and Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test all connections
python runpod_connections.py

# Test SSH connection specifically
python diagnose_ssh.py

# Check disk space on RunPod
python check_disk_space.py
```

### File Operations

```bash
# Interactive file transfer
python file_transfer.py

# Upload file via SSH
python file_transfer.py upload-ssh <local_file> [remote_path]

# Download file via SSH
python file_transfer.py download-ssh <remote_file> [local_path]

# Upload to S3
python file_transfer.py upload-s3 <local_file> [s3_key]

# Download from S3
python file_transfer.py download-s3 <s3_key> [local_path]

# List S3 files
python file_transfer.py list-s3 [prefix]
```

### ComfyUI Management

```bash
# Analyze disk space (dry run)
python cleanup_comfyui_space.py

# Execute cleanup (DESTRUCTIVE)
python cleanup_comfyui_space.py --execute

# Download workflow models
python download_workflow_models.py
```

### SSH Direct Access

```bash
# Execute command via SSH wrapper
python -c "from runpod_connections import RunPodConnections; r=RunPodConnections(); r.ssh_connect(); print(r.ssh_execute('nvidia-smi'))"
```

## Key Implementation Notes

### SSH Key Discovery Algorithm

The `_find_ssh_key()` method searches in this order:
1. Preferred key path (parameter)
2. Common key names in ~/.ssh: id_ed25519, id_rsa, id_ecdsa
3. Any file matching id_* pattern (excluding .pub files)

### Credential Parsing

The `_load_credentials()` method uses regex-based parsing:
- Extracts SSH user@host from ssh command patterns
- Finds port with `-p PORT` pattern
- Detects direct IP with `root@IP` pattern
- Normalizes S3 credential keys with aliases

### S3 Configuration

- Region: `us-ca-2`
- Endpoint: `https://s3api-us-ca-2.runpod.io`
- Uses boto3 with custom endpoint_url

### Error Handling

- SSH operations print [OK]/[ERROR] prefixed messages
- Connection failures return False/None rather than raising exceptions
- Verbose mode available for detailed error tracing
- Timeouts configured: 60s for subprocess, 30s for HTTP

## Directory Structure

```
runpod/
├── runpod_connections.py    # Core connection handler
├── runpod_config.py          # API configuration (environment-based)
├── runpod_client.py          # GraphQL API client
├── file_transfer.py          # File transfer CLI
├── download_workflow_models.py  # ComfyUI model downloader
├── cleanup_comfyui_space.py     # Disk cleanup utility
├── check_disk_space.py          # Disk analysis tool
├── diagnose_ssh.py              # SSH diagnostic tool
├── setup_env.py                 # Environment setup helper
├── env                          # Credentials (NOT .env)
├── requirements.txt             # Python dependencies
└── *.md                         # Documentation files
```

## Dependencies

Core dependencies in `requirements.txt`:
- `requests>=2.28.0` - HTTP client for API calls
- `python-dotenv>=1.0.0` - Environment variable loading
- `boto3>=1.26.0` - AWS S3 client
- `paramiko>=2.11.0` - SSH/SFTP client

## Important Caveats

1. **Credentials File**: The project uses `.env` following standard dotenv conventions
2. **SSH Keys**: RunPod instances require SSH key authentication (no password auth)
3. **Workspace Path**: All RunPod operations assume `/workspace` as the base directory
4. **Dry Run Default**: Cleanup operations default to dry-run mode for safety
5. **S3 vs SSH**: S3 persists when pod is stopped; SSH requires running pod
6. **Large Models**: Some workflow models are 10-20GB+ each; check disk space first

## Working with This Codebase

When adding new features:
- Extend `RunPodConnections` for new connection types
- Use the existing credential parsing system
- Follow the [OK]/[ERROR] message prefix pattern
- Add dry-run mode for destructive operations
- Include verbose mode for debugging
- Update relevant documentation files

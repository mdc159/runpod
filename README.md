# RunPod Multi-Connection Guide

This project helps you connect to RunPod using multiple methods based on your `.env` file credentials.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Your credentials are already set up!**
   The project automatically reads from your `.env` file which contains:
   - ✅ S3 Storage credentials (for file storage)
   - ✅ SSH connection details (for direct server access)

3. **Test your connections:**
   ```bash
   python runpod_connections.py
   ```

## 📁 Available Connection Methods

### 1. S3 Storage Connection
- **Purpose**: Store and retrieve files from RunPod's S3-compatible storage
- **Credentials**: AWS access keys and bucket info from your `.env` file
- **Use cases**: Model storage, dataset management, result storage

### 2. SSH Connection
- **Purpose**: Direct access to your RunPod server
- **Credentials**: SSH host and authentication from your `.env` file
- **Use cases**: Running commands, file transfers, real-time interaction

## 🔧 Usage Examples

### S3 Operations
```python
from runpod_connections import RunPodConnections

runpod = RunPodConnections()

# List files in your S3 bucket
files = runpod.list_s3_files()
print(f"Found {len(files)} files")

# Upload a file
runpod.upload_to_s3("local_file.txt", "remote_file.txt")

# Download a file
runpod.download_from_s3("remote_file.txt", "downloaded_file.txt")
```

### SSH Operations
```python
# Connect to your RunPod server
if runpod.ssh_connect():
    # Execute commands
    output, error = runpod.ssh_execute("nvidia-smi")
    print(f"GPU Status: {output}")
    
    # Upload files
    runpod.ssh_upload_file("local_file.txt", "/workspace/remote_file.txt")
    
    # Download files
    runpod.ssh_download_file("/workspace/remote_file.txt", "downloaded_file.txt")
    
    runpod.close_ssh()
```

### Combined Workflow
```python
# 1. Download model from S3
runpod.download_from_s3("models/my_model.pt", "local_model.pt")

# 2. Upload to RunPod server
runpod.ssh_connect()
runpod.ssh_upload_file("local_model.pt", "/workspace/model.pt")

# 3. Run inference
output, error = runpod.ssh_execute("python inference.py")

# 4. Save results back to S3
runpod.ssh_download_file("/workspace/results.txt", "results.txt")
runpod.upload_to_s3("results.txt", "results/inference_results.txt")
```

## 📊 Your Current Setup

Based on your `.env` file, you have:

- **S3 Bucket**: `qb32g9o3oa`
- **S3 Endpoint**: `https://s3api-us-ca-2.runpod.io`
- **SSH Host**: `ssh.runpod.io`
- **SSH User**: `im5qj03lqzxugv-64410c77`
- **Direct IP**: `149.36.1.233:40082`

## 🛠️ Files

- `runpod_connections.py` - Main multi-connection client
- `runpod_examples.py` - Usage examples and demos
- `runpod_config.py` - API configuration (for future use)
- `runpod_client.py` - API client (for future use)
- `requirements.txt` - Python dependencies
- `README.md` - This guide

## 🚀 Quick Commands

```bash
# Test all connections
python runpod_connections.py

# Run examples
python runpod_examples.py

# Test S3 operations
python -c "from runpod_connections import RunPodConnections; r=RunPodConnections(); print('Files:', len(r.list_s3_files()))"

# Test SSH connection
python -c "from runpod_connections import RunPodConnections; r=RunPodConnections(); print('SSH:', r.ssh_connect())"
```

## 🔧 Troubleshooting

1. **SSH Connection Issues**
   - Make sure your SSH key is at `~/.ssh/id_ed25519`
   - Check that your RunPod instance is running
   - Verify the SSH host and port are correct

2. **S3 Connection Issues**
   - Verify your AWS credentials in the `.env` file
   - Check that the bucket name and endpoint URL are correct
   - Ensure your RunPod instance has S3 access enabled

3. **Permission Issues**
   - Make sure your SSH key has the correct permissions: `chmod 600 ~/.ssh/id_ed25519`
   - Verify your S3 credentials have the necessary permissions

## 📚 Additional Resources

- [RunPod Documentation](https://docs.runpod.io/)
- [RunPod Console](https://console.runpod.io/)
- [S3 API Documentation](https://docs.aws.amazon.com/s3/)
- [SSH Key Management](https://docs.runpod.io/docs/ssh-keys)

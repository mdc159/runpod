# RunPod File Transfer Guide

Complete guide for transferring files to/from your RunPod instance.

## Quick Reference

| Method | Speed | Use Case | Requires Pod Running |
|--------|-------|----------|---------------------|
| **SSH/SFTP** | Fast | Direct pod access, any file | Yes ✅ |
| **S3 Storage** | Medium | Persistent storage, large files | No ❌ |
| **SCP** | Fast | Command-line file copy | Yes ✅ |
| **Python Script** | Fast | Automated transfers | Yes ✅ |

---

## Method 1: SSH/SFTP (Recommended for Direct Transfers)

### Using the Python Utility (Easiest)

#### Interactive Mode
```bash
python file_transfer.py
```
This gives you a menu to choose upload/download options.

#### Command Line Mode
```bash
# Upload a file
python file_transfer.py upload-ssh myfile.txt /workspace/

# Download a file
python file_transfer.py download-ssh /workspace/results.txt ./

# Upload entire directory
python file_transfer.py upload-dir ./mydata /workspace/data/
```

### Using SCP Directly

```bash
# Upload file to RunPod
scp myfile.txt runpod:/workspace/

# Upload multiple files
scp file1.txt file2.txt runpod:/workspace/

# Upload directory
scp -r ./mydir runpod:/workspace/

# Download file from RunPod
scp runpod:/workspace/results.txt ./

# Download directory
scp -r runpod:/workspace/output ./
```

### Using SFTP Directly

```bash
# Start SFTP session
sftp runpod

# SFTP commands:
sftp> pwd                    # Show remote directory
sftp> ls                     # List remote files
sftp> cd /workspace         # Change remote directory
sftp> put myfile.txt        # Upload file
sftp> get results.txt       # Download file
sftp> put -r mydir          # Upload directory
sftp> get -r output         # Download directory
sftp> exit                  # Close connection
```

### Using Python Script

```python
from runpod_connections import RunPodConnections

runpod = RunPodConnections()

# Connect
if runpod.ssh_connect():
    # Upload file
    runpod.ssh_upload_file("local_file.txt", "/workspace/remote_file.txt")

    # Download file
    runpod.ssh_download_file("/workspace/results.txt", "results.txt")

    # Close
    runpod.close_ssh()
```

---

## Method 2: S3 Storage (For Persistent Storage)

S3 storage persists even when your pod is stopped. Great for:
- Model weights
- Large datasets
- Results you want to keep

### Using the Python Utility

```bash
# Upload to S3
python file_transfer.py upload-s3 mymodel.pt models/mymodel.pt

# Download from S3
python file_transfer.py download-s3 models/mymodel.pt ./

# List S3 files
python file_transfer.py list-s3
python file_transfer.py list-s3 models/  # with prefix
```

### Using Python Script

```python
from runpod_connections import RunPodConnections

runpod = RunPodConnections()

# Upload to S3
runpod.upload_to_s3("local_model.pt", "models/my_model.pt")

# List files
files = runpod.list_s3_files("models/")
print(files)

# Download from S3
runpod.download_from_s3("models/my_model.pt", "downloaded_model.pt")
```

### Using AWS CLI

```bash
# List files
aws s3 ls --region us-ca-2 --endpoint-url https://s3api-us-ca-2.runpod.io s3://qb32g9o3oa/

# Upload file
aws s3 cp myfile.txt s3://qb32g9o3oa/ --region us-ca-2 --endpoint-url https://s3api-us-ca-2.runpod.io

# Download file
aws s3 cp s3://qb32g9o3oa/myfile.txt ./ --region us-ca-2 --endpoint-url https://s3api-us-ca-2.runpod.io

# Sync directory
aws s3 sync ./mydir s3://qb32g9o3oa/data/ --region us-ca-2 --endpoint-url https://s3api-us-ca-2.runpod.io
```

---

## Method 3: Combined Workflow (S3 + SSH)

For persistent storage that you can access from any pod:

### Store Model in S3, Load in Pod

```python
from runpod_connections import RunPodConnections

runpod = RunPodConnections()

# 1. Upload model to S3 (one-time)
runpod.upload_to_s3("local_model.pt", "models/my_model.pt")

# 2. Later, in any pod: download from S3 to pod
if runpod.ssh_connect():
    # Download S3 file directly on the pod
    runpod.ssh_execute("""
        aws s3 cp s3://qb32g9o3oa/models/my_model.pt /workspace/model.pt \
            --region us-ca-2 \
            --endpoint-url https://s3api-us-ca-2.runpod.io
    """)

    # Or download locally then upload via SSH
    runpod.download_from_s3("models/my_model.pt", "temp_model.pt")
    runpod.ssh_upload_file("temp_model.pt", "/workspace/model.pt")

    runpod.close_ssh()
```

---

## Common Use Cases

### 1. Upload Training Script and Data

```bash
# Upload script
scp train.py runpod:/workspace/

# Upload dataset directory
scp -r ./dataset runpod:/workspace/data/

# Or using Python
python file_transfer.py upload-ssh train.py /workspace/
```

### 2. Download Training Results

```bash
# Download results
scp runpod:/workspace/checkpoints/model_final.pt ./

# Download logs
scp runpod:/workspace/train.log ./

# Or using Python
python file_transfer.py download-ssh /workspace/checkpoints/model_final.pt ./
```

### 3. Sync Code Changes During Development

```bash
# Upload updated code
scp src/*.py runpod:/workspace/src/

# Or sync entire directory
rsync -avz -e ssh ./src/ runpod:/workspace/src/
```

### 4. Large File Transfer via S3

For very large files (>1GB), S3 is more reliable:

```bash
# 1. Upload to S3
python file_transfer.py upload-s3 large_dataset.tar.gz datasets/

# 2. SSH to pod and download from S3
ssh runpod "cd /workspace && aws s3 cp s3://qb32g9o3oa/datasets/large_dataset.tar.gz . --region us-ca-2 --endpoint-url https://s3api-us-ca-2.runpod.io"

# 3. Extract on pod
ssh runpod "cd /workspace && tar -xzf large_dataset.tar.gz"
```

---

## Troubleshooting

### SSH Transfer Fails: "Container not found"

**Problem**: Your pod is not running

**Solution**:
1. Go to https://console.runpod.io/
2. Start/resume your pod
3. Try transfer again

### S3 Transfer Fails: Authentication Error

**Problem**: S3 credentials incorrect

**Solution**:
1. Check your [.env](.env) file has correct credentials
2. Verify credentials at https://console.runpod.io/user/settings

### Large Files Transfer Slowly

**Solutions**:
- Use S3 instead of SSH for files >100MB
- Compress files before transfer: `tar -czf data.tar.gz ./data/`
- Use `rsync` with compression: `rsync -avz -e ssh ./data/ runpod:/workspace/data/`

### Connection Times Out

**Problem**: Pod is stopped or network issue

**Solution**:
1. Check pod status at https://console.runpod.io/
2. Try S3 transfer (works even when pod is stopped)
3. Run diagnostic: `python diagnose_ssh.py`

---

## Performance Tips

### 1. Compress Before Transfer
```bash
# Create compressed archive
tar -czf mydata.tar.gz ./mydata/

# Transfer compressed file
scp mydata.tar.gz runpod:/workspace/

# Extract on pod
ssh runpod "cd /workspace && tar -xzf mydata.tar.gz"
```

### 2. Parallel Transfers
```bash
# Upload multiple files in parallel
for file in *.txt; do
    scp "$file" runpod:/workspace/ &
done
wait
```

### 3. Resume Interrupted Transfers
```bash
# Use rsync to resume
rsync -avz --partial -e ssh large_file.bin runpod:/workspace/
```

---

## Files Created

1. **[file_transfer.py](file_transfer.py)** - Interactive file transfer utility
   - Run: `python file_transfer.py`
   - Supports SSH and S3 transfers
   - Interactive menu or command-line mode

2. **[runpod_connections.py](runpod_connections.py)** - Connection library
   - Import and use in your own scripts
   - Handles SSH and S3 connections

---

## Quick Commands Reference

```bash
# Interactive transfer tool
python file_transfer.py

# SSH upload
scp myfile.txt runpod:/workspace/

# SSH download
scp runpod:/workspace/results.txt ./

# Directory upload
scp -r ./mydir runpod:/workspace/

# S3 upload
python file_transfer.py upload-s3 myfile.txt

# S3 list
python file_transfer.py list-s3

# Check connection
python diagnose_ssh.py
```

---

## Next Steps

1. **Start your pod**: https://console.runpod.io/
2. **Test connection**: `python diagnose_ssh.py`
3. **Transfer files**: `python file_transfer.py`
4. **Run your workload**: `ssh runpod "python /workspace/train.py"`

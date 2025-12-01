"""
RunPod Usage Examples
This file demonstrates how to use the different RunPod connection methods.
"""

from runpod_connections import RunPodConnections
import os

def example_s3_operations():
    """Example of S3 operations."""
    print("🗄️  S3 Operations Example")
    print("-" * 30)
    
    runpod = RunPodConnections()
    
    # List files in bucket
    print("📋 Listing files in S3 bucket...")
    files = runpod.list_s3_files()
    print(f"Found {len(files)} files")
    
    # Upload a file (example)
    # runpod.upload_to_s3("local_file.txt", "remote_file.txt")
    
    # Download a file (example)
    # runpod.download_from_s3("remote_file.txt", "downloaded_file.txt")

def example_ssh_operations():
    """Example of SSH operations."""
    print("🔐 SSH Operations Example")
    print("-" * 30)
    
    runpod = RunPodConnections()
    
    # Connect via SSH
    if runpod.ssh_connect():
        print("✅ Connected to RunPod via SSH")
        
        # Execute commands
        print("\n📊 System Information:")
        output, error = runpod.ssh_execute("uname -a")
        if output:
            print(f"OS: {output.strip()}")
        
        output, error = runpod.ssh_execute("df -h")
        if output:
            print(f"Disk Usage:\n{output}")
        
        output, error = runpod.ssh_execute("nvidia-smi")
        if output:
            print(f"GPU Status:\n{output}")
        elif error and "command not found" not in error:
            print(f"GPU Info: {error}")
        
        # File operations
        print("\n📁 File Operations:")
        output, error = runpod.ssh_execute("ls -la /workspace")
        if output:
            print(f"Workspace contents:\n{output}")
        
        # Upload a file (example)
        # runpod.ssh_upload_file("local_file.txt", "/workspace/remote_file.txt")
        
        # Download a file (example)
        # runpod.ssh_download_file("/workspace/remote_file.txt", "downloaded_file.txt")
        
        runpod.close_ssh()
    else:
        print("❌ SSH connection failed")

def example_combined_workflow():
    """Example of combining S3 and SSH operations."""
    print("🔄 Combined Workflow Example")
    print("-" * 30)
    
    runpod = RunPodConnections()
    
    # 1. Download a file from S3
    print("1️⃣  Downloading file from S3...")
    # runpod.download_from_s3("model.pt", "local_model.pt")
    
    # 2. Upload to RunPod via SSH
    print("2️⃣  Uploading to RunPod...")
    if runpod.ssh_connect():
        # runpod.ssh_upload_file("local_model.pt", "/workspace/model.pt")
        
        # 3. Run inference on RunPod
        print("3️⃣  Running inference...")
        output, error = runpod.ssh_execute("python inference_script.py")
        if output:
            print(f"Inference output: {output}")
        
        # 4. Download results back to S3
        print("4️⃣  Uploading results to S3...")
        # runpod.ssh_download_file("/workspace/results.txt", "results.txt")
        # runpod.upload_to_s3("results.txt", "results/results.txt")
        
        runpod.close_ssh()

def main():
    """Run all examples."""
    print("🚀 RunPod Connection Examples")
    print("=" * 50)
    
    # Show connection info
    runpod = RunPodConnections()
    info = runpod.get_connection_info()
    
    print("📊 Available Connections:")
    print(f"  S3 Storage: {'✅' if info['s3_available'] else '❌'}")
    print(f"  SSH Access: {'✅' if info['ssh_available'] else '❌'}")
    
    if info['s3_available']:
        example_s3_operations()
        print()
    
    if info['ssh_available']:
        example_ssh_operations()
        print()
    
    if info['s3_available'] and info['ssh_available']:
        example_combined_workflow()

if __name__ == "__main__":
    main()


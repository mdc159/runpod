"""
RunPod File Transfer Helper
Easy file upload/download to your RunPod instance
"""

import sys
import os
from pathlib import Path
from runpod_connections import RunPodConnections

def upload_file(local_path: str, remote_path: str = None):
    """Upload a file to RunPod."""
    if not os.path.exists(local_path):
        print(f"❌ Local file not found: {local_path}")
        return False

    if remote_path is None:
        # Default to /workspace/ with same filename
        filename = os.path.basename(local_path)
        remote_path = f"/workspace/{filename}"

    print(f"📤 Uploading {local_path} -> {remote_path}")

    runpod = RunPodConnections()
    success = runpod.ssh_upload_file(local_path, remote_path)
    runpod.close_ssh()

    return success

def download_file(remote_path: str, local_path: str = None):
    """Download a file from RunPod."""
    if local_path is None:
        # Default to current directory with same filename
        filename = os.path.basename(remote_path)
        local_path = filename

    print(f"📥 Downloading {remote_path} -> {local_path}")

    runpod = RunPodConnections()
    success = runpod.ssh_download_file(remote_path, local_path)
    runpod.close_ssh()

    return success

def upload_directory(local_dir: str, remote_dir: str = "/workspace/"):
    """Upload all files in a directory to RunPod."""
    local_path = Path(local_dir)

    if not local_path.exists() or not local_path.is_dir():
        print(f"❌ Local directory not found: {local_dir}")
        return False

    print(f"📤 Uploading directory {local_dir} -> {remote_dir}")

    runpod = RunPodConnections()
    if not runpod.ssh_connect():
        return False

    # Create remote directory
    runpod.ssh_execute(f"mkdir -p {remote_dir}")

    # Upload all files
    success_count = 0
    total_files = 0

    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            total_files += 1
            relative_path = file_path.relative_to(local_path)
            remote_file = os.path.join(remote_dir, str(relative_path)).replace("\\", "/")

            # Create remote subdirectory if needed
            remote_subdir = os.path.dirname(remote_file)
            runpod.ssh_execute(f"mkdir -p {remote_subdir}")

            print(f"  📄 {relative_path}")
            if runpod.ssh_upload_file(str(file_path), remote_file):
                success_count += 1

    runpod.close_ssh()

    print(f"\n✅ Uploaded {success_count}/{total_files} files")
    return success_count == total_files

def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print("""
RunPod File Transfer Helper

Usage:
  python transfer_files.py upload <local_file> [remote_path]
  python transfer_files.py download <remote_file> [local_path]
  python transfer_files.py upload-dir <local_directory> [remote_directory]

Examples:
  # Upload a file
  python transfer_files.py upload model.pt /workspace/model.pt

  # Download a file
  python transfer_files.py download /workspace/results.txt ./results.txt

  # Upload entire directory
  python transfer_files.py upload-dir ./my_project /workspace/my_project
        """)
        return

    command = sys.argv[1].lower()

    if command == "upload" and len(sys.argv) >= 3:
        local_path = sys.argv[2]
        remote_path = sys.argv[3] if len(sys.argv) > 3 else None
        upload_file(local_path, remote_path)

    elif command == "download" and len(sys.argv) >= 3:
        remote_path = sys.argv[2]
        local_path = sys.argv[3] if len(sys.argv) > 3 else None
        download_file(remote_path, local_path)

    elif command == "upload-dir" and len(sys.argv) >= 3:
        local_dir = sys.argv[2]
        remote_dir = sys.argv[3] if len(sys.argv) > 3 else "/workspace/"
        upload_directory(local_dir, remote_dir)

    else:
        print("❌ Invalid command. Use: upload, download, or upload-dir")

if __name__ == "__main__":
    main()

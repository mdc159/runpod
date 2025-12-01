"""
RunPod File Transfer Utility
Multiple methods to transfer files to/from RunPod
"""

import os
import sys
from pathlib import Path
from runpod_connections import RunPodConnections


class RunPodFileTransfer:
    """Handles file transfers to/from RunPod using multiple methods."""

    def __init__(self):
        self.runpod = RunPodConnections(verbose=True)

    def upload_via_ssh(self, local_path, remote_path="/workspace/"):
        """
        Upload file via SSH/SFTP.

        Args:
            local_path: Path to local file
            remote_path: Destination path on RunPod (default: /workspace/)
        """
        print(f"\n[SSH Upload] Transferring {local_path} to {remote_path}")

        if not os.path.exists(local_path):
            print(f"[ERROR] Local file not found: {local_path}")
            return False

        # Connect if not already connected
        if not self.runpod.ssh_client:
            if not self.runpod.ssh_connect():
                print("[ERROR] Failed to establish SSH connection")
                return False

        # If remote_path is a directory, append filename
        if remote_path.endswith('/'):
            filename = os.path.basename(local_path)
            remote_path = os.path.join(remote_path, filename)

        return self.runpod.ssh_upload_file(local_path, remote_path)

    def download_via_ssh(self, remote_path, local_path="./"):
        """
        Download file via SSH/SFTP.

        Args:
            remote_path: Path to file on RunPod
            local_path: Destination path locally (default: current directory)
        """
        print(f"\n[SSH Download] Transferring {remote_path} to {local_path}")

        # Connect if not already connected
        if not self.runpod.ssh_client:
            if not self.runpod.ssh_connect():
                print("[ERROR] Failed to establish SSH connection")
                return False

        # If local_path is a directory, append filename
        if local_path.endswith('/') or os.path.isdir(local_path):
            filename = os.path.basename(remote_path)
            local_path = os.path.join(local_path, filename)

        return self.runpod.ssh_download_file(remote_path, local_path)

    def upload_via_s3(self, local_path, s3_key=None):
        """
        Upload file to RunPod S3 storage.

        Args:
            local_path: Path to local file
            s3_key: S3 key (path in bucket). If None, uses filename
        """
        print(f"\n[S3 Upload] Transferring {local_path} to S3")

        if not os.path.exists(local_path):
            print(f"[ERROR] Local file not found: {local_path}")
            return False

        if s3_key is None:
            s3_key = os.path.basename(local_path)

        return self.runpod.upload_to_s3(local_path, s3_key)

    def download_via_s3(self, s3_key, local_path=None):
        """
        Download file from RunPod S3 storage.

        Args:
            s3_key: S3 key (path in bucket)
            local_path: Destination path locally. If None, uses s3_key basename
        """
        print(f"\n[S3 Download] Transferring {s3_key} from S3")

        if local_path is None:
            local_path = os.path.basename(s3_key)

        return self.runpod.download_from_s3(s3_key, local_path)

    def list_s3_files(self, prefix=""):
        """List files in S3 bucket."""
        print(f"\n[S3 List] Files in bucket (prefix: '{prefix}')")
        files = self.runpod.list_s3_files(prefix)

        if files:
            print(f"Found {len(files)} file(s):")
            for f in files:
                print(f"  - {f}")
        else:
            print("No files found")

        return files

    def upload_directory_ssh(self, local_dir, remote_dir="/workspace/"):
        """
        Upload entire directory via SSH.

        Args:
            local_dir: Local directory path
            remote_dir: Remote directory path
        """
        print(f"\n[SSH Upload Dir] Transferring directory {local_dir} to {remote_dir}")

        if not os.path.isdir(local_dir):
            print(f"[ERROR] Local directory not found: {local_dir}")
            return False

        # Connect if not already connected
        if not self.runpod.ssh_client:
            if not self.runpod.ssh_connect():
                print("[ERROR] Failed to establish SSH connection")
                return False

        try:
            sftp = self.runpod.ssh_client.open_sftp()

            # Create remote directory if it doesn't exist
            try:
                sftp.stat(remote_dir)
            except:
                print(f"Creating remote directory: {remote_dir}")
                sftp.mkdir(remote_dir)

            # Upload all files
            success_count = 0
            error_count = 0

            for root, dirs, files in os.walk(local_dir):
                # Calculate relative path
                rel_path = os.path.relpath(root, local_dir)

                # Create subdirectories
                for dir_name in dirs:
                    if rel_path == '.':
                        remote_subdir = os.path.join(remote_dir, dir_name)
                    else:
                        remote_subdir = os.path.join(remote_dir, rel_path, dir_name)

                    remote_subdir = remote_subdir.replace('\\', '/')

                    try:
                        sftp.stat(remote_subdir)
                    except:
                        print(f"Creating directory: {remote_subdir}")
                        sftp.mkdir(remote_subdir)

                # Upload files
                for filename in files:
                    local_file = os.path.join(root, filename)

                    if rel_path == '.':
                        remote_file = os.path.join(remote_dir, filename)
                    else:
                        remote_file = os.path.join(remote_dir, rel_path, filename)

                    remote_file = remote_file.replace('\\', '/')

                    try:
                        print(f"Uploading: {local_file} -> {remote_file}")
                        sftp.put(local_file, remote_file)
                        success_count += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to upload {local_file}: {e}")
                        error_count += 1

            sftp.close()
            print(f"\n[SUCCESS] Uploaded {success_count} file(s), {error_count} error(s)")
            return error_count == 0

        except Exception as e:
            print(f"[ERROR] Directory upload failed: {e}")
            return False

    def close(self):
        """Close connections."""
        self.runpod.close_ssh()


def print_menu():
    """Print the main menu."""
    print("\n" + "="*70)
    print("RunPod File Transfer Utility")
    print("="*70)
    print("\nOptions:")
    print("  1. Upload file via SSH")
    print("  2. Download file via SSH")
    print("  3. Upload directory via SSH")
    print("  4. Upload file to S3")
    print("  5. Download file from S3")
    print("  6. List S3 files")
    print("  7. Exit")
    print()


def main():
    """Interactive file transfer menu."""
    transfer = RunPodFileTransfer()

    while True:
        print_menu()
        choice = input("Select an option (1-7): ").strip()

        if choice == '1':
            local_path = input("Local file path: ").strip()
            remote_path = input("Remote path (default: /workspace/): ").strip() or "/workspace/"
            transfer.upload_via_ssh(local_path, remote_path)

        elif choice == '2':
            remote_path = input("Remote file path: ").strip()
            local_path = input("Local destination (default: ./): ").strip() or "./"
            transfer.download_via_ssh(remote_path, local_path)

        elif choice == '3':
            local_dir = input("Local directory path: ").strip()
            remote_dir = input("Remote directory (default: /workspace/): ").strip() or "/workspace/"
            transfer.upload_directory_ssh(local_dir, remote_dir)

        elif choice == '4':
            local_path = input("Local file path: ").strip()
            s3_key = input("S3 key (leave empty to use filename): ").strip() or None
            transfer.upload_via_s3(local_path, s3_key)

        elif choice == '5':
            s3_key = input("S3 key: ").strip()
            local_path = input("Local destination (leave empty to use S3 filename): ").strip() or None
            transfer.download_via_s3(s3_key, local_path)

        elif choice == '6':
            prefix = input("Prefix (leave empty for all files): ").strip()
            transfer.list_s3_files(prefix)

        elif choice == '7':
            print("\nClosing connections...")
            transfer.close()
            print("Goodbye!")
            break

        else:
            print("[ERROR] Invalid option. Please select 1-7.")


if __name__ == "__main__":
    # If arguments provided, use command-line mode
    if len(sys.argv) > 1:
        transfer = RunPodFileTransfer()

        if sys.argv[1] == 'upload-ssh' and len(sys.argv) >= 3:
            local = sys.argv[2]
            remote = sys.argv[3] if len(sys.argv) > 3 else "/workspace/"
            transfer.upload_via_ssh(local, remote)

        elif sys.argv[1] == 'download-ssh' and len(sys.argv) >= 3:
            remote = sys.argv[2]
            local = sys.argv[3] if len(sys.argv) > 3 else "./"
            transfer.download_via_ssh(remote, local)

        elif sys.argv[1] == 'upload-s3' and len(sys.argv) >= 3:
            local = sys.argv[2]
            s3_key = sys.argv[3] if len(sys.argv) > 3 else None
            transfer.upload_via_s3(local, s3_key)

        elif sys.argv[1] == 'download-s3' and len(sys.argv) >= 3:
            s3_key = sys.argv[2]
            local = sys.argv[3] if len(sys.argv) > 3 else None
            transfer.download_via_s3(s3_key, local)

        elif sys.argv[1] == 'list-s3':
            prefix = sys.argv[2] if len(sys.argv) > 2 else ""
            transfer.list_s3_files(prefix)

        else:
            print("Usage:")
            print("  python file_transfer.py upload-ssh <local_file> [remote_path]")
            print("  python file_transfer.py download-ssh <remote_file> [local_path]")
            print("  python file_transfer.py upload-s3 <local_file> [s3_key]")
            print("  python file_transfer.py download-s3 <s3_key> [local_path]")
            print("  python file_transfer.py list-s3 [prefix]")
            print("\nOr run without arguments for interactive mode:")
            print("  python file_transfer.py")

        transfer.close()
    else:
        # Interactive mode
        main()

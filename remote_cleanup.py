#!/usr/bin/env python3
"""
Remote cleanup script for RunPod ComfyUI instances.
Executes cleanup commands via SSH.
"""

import subprocess
import sys
from pathlib import Path
from runpod_config import get_pod_config


def execute_ssh_command(host, port, command, private_key_path=None):
    """Execute a command via SSH and return output."""
    ssh_key_arg = f"-i {private_key_path}" if private_key_path else ""

    ssh_cmd = [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
    ]

    if private_key_path:
        ssh_cmd.extend(["-i", private_key_path])

    ssh_cmd.append(f"root@{host}")
    ssh_cmd.append(command)

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1


def check_disk_space(host, port, private_key_path=None):
    """Check disk space on remote host."""
    print("\n" + "=" * 80)
    print("CHECKING DISK SPACE")
    print("=" * 80)

    commands = [
        ("Overall disk usage", "df -h /workspace"),
        ("ComfyUI size", "du -sh /workspace/ComfyUI 2>/dev/null || echo 'N/A'"),
        ("Models directory", "du -sh /workspace/ComfyUI/models 2>/dev/null || echo 'N/A'"),
        ("Output directory", "du -sh /workspace/ComfyUI/output 2>/dev/null || echo 'N/A'"),
    ]

    for description, command in commands:
        print(f"\n{description}:")
        stdout, stderr, returncode = execute_ssh_command(host, port, command, private_key_path)
        if returncode == 0:
            print(stdout)
        else:
            print(f"Error: {stderr}")


def find_temp_files(host, port, private_key_path=None):
    """Find temporary files."""
    print("\n" + "=" * 80)
    print("FINDING TEMPORARY FILES")
    print("=" * 80)

    commands = [
        ("*.part files", "find /workspace/ComfyUI -type f -name '*.part' 2>/dev/null | wc -l"),
        ("*.tmp files", "find /workspace/ComfyUI -type f -name '*.tmp' 2>/dev/null | wc -l"),
        ("*.temp files", "find /workspace/ComfyUI -type f -name '*.temp' 2>/dev/null | wc -l"),
    ]

    for description, command in commands:
        print(f"\n{description}:")
        stdout, stderr, returncode = execute_ssh_command(host, port, command, private_key_path)
        if returncode == 0:
            count = stdout.strip()
            print(f"  Found: {count} files")
        else:
            print(f"  Error: {stderr}")


def cleanup_temp_files(host, port, private_key_path=None, dry_run=True):
    """Clean up temporary files."""
    print("\n" + "=" * 80)
    print("CLEANING TEMPORARY FILES" + (" (DRY RUN)" if dry_run else " (EXECUTING)"))
    print("=" * 80)

    if dry_run:
        # Just list files
        commands = [
            ("*.part files", "find /workspace/ComfyUI -type f -name '*.part' -ls 2>/dev/null"),
            ("*.tmp files", "find /workspace/ComfyUI -type f -name '*.tmp' -ls 2>/dev/null"),
        ]
    else:
        # Actually delete
        commands = [
            ("*.part files", "find /workspace/ComfyUI -type f -name '*.part' -delete && echo 'Deleted'"),
            ("*.tmp files", "find /workspace/ComfyUI -type f -name '*.tmp' -delete && echo 'Deleted'"),
            ("*.temp files", "find /workspace/ComfyUI -type f -name '*.temp' -delete && echo 'Deleted'"),
        ]

    for description, command in commands:
        print(f"\n{description}:")
        stdout, stderr, returncode = execute_ssh_command(host, port, command, private_key_path)
        if returncode == 0:
            print(stdout if stdout else "  No files found")
        else:
            print(f"  Error: {stderr}")


def cleanup_cache(host, port, private_key_path=None, dry_run=True):
    """Clean up ComfyUI cache."""
    print("\n" + "=" * 80)
    print("CLEANING COMFYUI CACHE" + (" (DRY RUN)" if dry_run else " (EXECUTING)"))
    print("=" * 80)

    cache_path = "/workspace/ComfyUI/user/default/ComfyUI-Manager/cache"

    # Check size first
    size_cmd = f"du -sh {cache_path} 2>/dev/null || echo 'N/A'"
    stdout, stderr, returncode = execute_ssh_command(host, port, size_cmd, private_key_path)
    print(f"Cache size: {stdout.strip()}")

    if not dry_run:
        # Delete cache
        delete_cmd = f"rm -rf {cache_path}/*"
        stdout, stderr, returncode = execute_ssh_command(host, port, delete_cmd, private_key_path)
        if returncode == 0:
            print("Cache cleared successfully")
        else:
            print(f"Error clearing cache: {stderr}")


def find_large_files(host, port, private_key_path=None, min_size_gb=5):
    """Find large model files."""
    print("\n" + "=" * 80)
    print(f"FINDING FILES LARGER THAN {min_size_gb}GB")
    print("=" * 80)

    command = f"find /workspace/ComfyUI/models -type f -size +{min_size_gb}G -exec ls -lh {{}} \\; 2>/dev/null | awk '{{print $5, $9}}' | sort -hr"
    stdout, stderr, returncode = execute_ssh_command(host, port, command, private_key_path)

    if returncode == 0 and stdout.strip():
        print(stdout)
    else:
        print(f"No files larger than {min_size_gb}GB found")


def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("RunPod ComfyUI Remote Cleanup Tool")
    print("=" * 80)

    # Get pod configuration
    try:
        config = get_pod_config()
        host = config.get('ssh_host')
        port = config.get('ssh_port')
        private_key_path = config.get('ssh_key_path')

        if not host or not port:
            print("\nError: Could not get pod configuration from runpod_config.py")
            print("Please ensure your pod is running and configured correctly.")
            sys.exit(1)

        print(f"\nConnecting to: {host}:{port}")

    except Exception as e:
        print(f"\nError loading configuration: {e}")
        print("\nPlease provide connection details manually:")
        host = input("SSH Host: ")
        port = input("SSH Port: ")
        private_key_path = input("Private key path (or press Enter for default): ").strip()
        if not private_key_path:
            private_key_path = None

    # Determine mode
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        dry_run = False
        print("\n⚠️  EXECUTE MODE - Files will be permanently deleted!")
        print("Press Ctrl+C within 5 seconds to cancel...\n")
        import time
        time.sleep(5)
    else:
        print("\n🔍 DRY RUN MODE - No files will be deleted")
        print("Run with --execute flag to actually delete files\n")

    # Run diagnostics and cleanup
    try:
        check_disk_space(host, port, private_key_path)
        find_temp_files(host, port, private_key_path)
        cleanup_temp_files(host, port, private_key_path, dry_run)
        cleanup_cache(host, port, private_key_path, dry_run)
        find_large_files(host, port, private_key_path)

        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print("""
1. Review large files and delete unused models
2. Clear output folder if images are not needed:
   ssh root@{host} -p {port} "rm -rf /workspace/ComfyUI/output/*"

3. For the Qwen model issue:
   - You already have the FP8 model (20.4GB) successfully downloaded
   - Consider using that instead of downloading the 14.9GB GGUF model
   - If you need the GGUF model, delete the FP8 version first to free space

4. To increase storage, stop the pod and increase container disk in RunPod dashboard
""".format(host=host, port=port))

        if dry_run:
            print("\n⚠️  This was a DRY RUN - no files were deleted.")
            print("Run with --execute flag to actually clean up files:")
            print(f"  python {Path(__file__).name} --execute")

        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

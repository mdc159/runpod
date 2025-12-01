#!/usr/bin/env python3
"""
ComfyUI Disk Space Fix - All-in-One Solution
Combines diagnostic and cleanup functionality with guided workflow.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title):
    """Print formatted section."""
    print(f"\n{'─' * 80}")
    print(f" {title}")
    print(f"{'─' * 80}")


def get_runpod_connection():
    """Get RunPod connection details."""
    try:
        from runpod_config import get_pod_config
        config = get_pod_config()
        return config.get('ssh_host'), config.get('ssh_port'), config.get('ssh_key_path')
    except:
        return None, None, None


def execute_remote_command(host, port, command, ssh_key=None, timeout=60):
    """Execute command on remote host."""
    ssh_cmd = [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10"
    ]

    if ssh_key:
        ssh_cmd.extend(["-i", ssh_key])

    ssh_cmd.append(f"root@{host}")
    ssh_cmd.append(command)

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1


def show_disk_usage(host, port, ssh_key=None):
    """Show current disk usage."""
    print_section("Current Disk Usage")

    stdout, stderr, rc = execute_remote_command(host, port, "df -h /workspace | tail -n 1", ssh_key)

    if rc == 0:
        parts = stdout.split()
        if len(parts) >= 5:
            total = parts[1]
            used = parts[2]
            available = parts[3]
            percent = parts[4]

            print(f"Total Space:     {total}")
            print(f"Used Space:      {used}")
            print(f"Available Space: {available}")
            print(f"Usage:           {percent}")

            # Parse percentage
            try:
                usage_pct = int(percent.rstrip('%'))
                if usage_pct > 90:
                    print(f"\n⚠️  WARNING: Disk usage is critically high ({percent})!")
                    print("   Immediate cleanup recommended.")
                elif usage_pct > 80:
                    print(f"\n⚠️  CAUTION: Disk usage is high ({percent}).")
                    print("   Consider cleanup soon.")
                else:
                    print(f"\n✅ Disk usage is acceptable ({percent}).")
            except:
                pass
        else:
            print(stdout)
    else:
        print(f"Error checking disk usage: {stderr}")

    return rc == 0


def check_comfyui_model(host, port, ssh_key=None):
    """Check if FP8 model exists."""
    print_section("Checking Qwen Model Status")

    fp8_model = "/workspace/ComfyUI/models/diffusion_models/qwen-image-edit/qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    gguf_model_path = "/workspace/ComfyUI/models/gguf"

    # Check FP8 model
    stdout, stderr, rc = execute_remote_command(
        host, port,
        f"test -f '{fp8_model}' && ls -lh '{fp8_model}' || echo 'NOT_FOUND'",
        ssh_key
    )

    if "NOT_FOUND" not in stdout:
        print("✅ FP8 Model: Found")
        print(f"   {stdout}")
        print("\n   This model is ready to use!")
        fp8_exists = True
    else:
        print("❌ FP8 Model: Not found")
        fp8_exists = False

    # Check for partial GGUF downloads
    stdout, stderr, rc = execute_remote_command(
        host, port,
        f"find {gguf_model_path} -name '*Qwen*.gguf*' -o -name '*.part' 2>/dev/null | head -10",
        ssh_key
    )

    if stdout:
        print("\n⚠️  Partial/Complete GGUF files found:")
        for line in stdout.split('\n'):
            if line.strip():
                # Get file size
                size_out, _, _ = execute_remote_command(host, port, f"ls -lh '{line.strip()}'", ssh_key)
                print(f"   {size_out}")
        gguf_partial = True
    else:
        print("\n✅ No partial GGUF downloads found")
        gguf_partial = False

    return fp8_exists, gguf_partial


def find_large_files(host, port, ssh_key=None):
    """Find and display large files."""
    print_section("Large Files Analysis")

    # Find files > 5GB
    stdout, stderr, rc = execute_remote_command(
        host, port,
        "find /workspace/ComfyUI -type f -size +5G -exec ls -lh {} \\; 2>/dev/null | awk '{print $5, $9}' | sort -rh",
        ssh_key,
        timeout=120
    )

    if stdout:
        print("Files larger than 5GB:\n")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"   {line}")
    else:
        print("No files larger than 5GB found.")


def count_temp_files(host, port, ssh_key=None):
    """Count temporary files."""
    print_section("Temporary Files")

    patterns = [
        ("Partial downloads (*.part)", "*.part"),
        ("Temporary files (*.tmp)", "*.tmp"),
        ("Temp files (*.temp)", "*.temp"),
    ]

    total_count = 0
    for description, pattern in patterns:
        stdout, stderr, rc = execute_remote_command(
            host, port,
            f"find /workspace/ComfyUI -type f -name '{pattern}' 2>/dev/null | wc -l",
            ssh_key
        )
        count = int(stdout) if stdout.isdigit() else 0
        total_count += count
        status = "⚠️ " if count > 0 else "✅"
        print(f"{status} {description}: {count} files")

    return total_count


def cleanup_temp_files(host, port, ssh_key=None, execute=False):
    """Clean up temporary files."""
    print_section("Cleanup Temporary Files" + (" [EXECUTING]" if execute else " [DRY RUN]"))

    if not execute:
        print("Preview of files to be deleted:\n")

    patterns = ["*.part", "*.tmp", "*.temp"]

    for pattern in patterns:
        if execute:
            stdout, stderr, rc = execute_remote_command(
                host, port,
                f"find /workspace/ComfyUI -type f -name '{pattern}' -delete 2>/dev/null && echo 'Deleted {pattern} files'",
                ssh_key
            )
            print(f"✅ {stdout}")
        else:
            stdout, stderr, rc = execute_remote_command(
                host, port,
                f"find /workspace/ComfyUI -type f -name '{pattern}' -ls 2>/dev/null | head -10",
                ssh_key
            )
            if stdout:
                print(f"\n{pattern} files:")
                for line in stdout.split('\n')[:5]:
                    if line.strip():
                        print(f"   {line}")


def cleanup_cache(host, port, ssh_key=None, execute=False):
    """Clean up ComfyUI cache."""
    print_section("Cleanup ComfyUI Cache" + (" [EXECUTING]" if execute else " [DRY RUN]"))

    cache_path = "/workspace/ComfyUI/user/default/ComfyUI-Manager/cache"

    # Check size
    stdout, stderr, rc = execute_remote_command(
        host, port,
        f"du -sh {cache_path} 2>/dev/null || echo 'N/A'",
        ssh_key
    )
    print(f"Cache size: {stdout}")

    if execute:
        stdout, stderr, rc = execute_remote_command(
            host, port,
            f"rm -rf {cache_path}/* && echo 'Cache cleared'",
            ssh_key
        )
        print(f"✅ {stdout}")
    else:
        print("   (Will clear cache contents)")


def show_recommendations(fp8_exists, gguf_partial):
    """Show recommendations based on findings."""
    print_header("RECOMMENDATIONS")

    if fp8_exists:
        print("""
✅ RECOMMENDATION: Use the FP8 model you already have!

The FP8 model (qwen_image_edit_2509_fp8_e4m3fn.safetensors) is already
downloaded and ready to use. This is a high-quality model suitable for
your ComfyUI workflows.

To use it:
1. Open your ComfyUI workflow
2. Update the model loader to point to the FP8 model
3. No additional downloads needed!
""")

    if gguf_partial:
        print("""
⚠️  PARTIAL GGUF DOWNLOAD DETECTED

You have incomplete GGUF model downloads. These are taking up space
without being usable.

Options:
A) Delete the partial GGUF files and use the FP8 model
B) Clear space and retry the GGUF download

To delete partial GGUF files:
   find /workspace/ComfyUI/models/gguf -name '*Qwen*.part' -delete
""")

    print("""
📋 GENERAL RECOMMENDATIONS:

1. Free up space by:
   - Removing temporary files (*.part, *.tmp)
   - Clearing old outputs if not needed
   - Removing ComfyUI-Manager cache
   - Deleting unused models

2. Prevent future issues:
   - Check disk space before large downloads (df -h /workspace)
   - Regularly clean output folder
   - Keep only models you actively use
   - Consider upgrading RunPod storage if working with many large models

3. To increase storage:
   - Stop your RunPod pod
   - Go to pod settings in RunPod dashboard
   - Increase "Container Disk" size
   - Restart pod
""")


def interactive_menu(host, port, ssh_key):
    """Show interactive menu."""
    while True:
        print_header("ComfyUI Disk Space Fix - Main Menu")
        print("""
1. Check disk usage
2. Analyze files (temp files, large files, models)
3. Clean up temporary files (DRY RUN)
4. Clean up temporary files (EXECUTE)
5. Clean up cache (DRY RUN)
6. Clean up cache (EXECUTE)
7. Full cleanup (EXECUTE ALL)
8. Show recommendations
9. Exit

Choose an option (1-9):""", end=" ")

        choice = input().strip()

        if choice == "1":
            show_disk_usage(host, port, ssh_key)
        elif choice == "2":
            fp8, gguf = check_comfyui_model(host, port, ssh_key)
            count_temp_files(host, port, ssh_key)
            find_large_files(host, port, ssh_key)
        elif choice == "3":
            cleanup_temp_files(host, port, ssh_key, execute=False)
        elif choice == "4":
            print("\n⚠️  This will DELETE files. Continue? (yes/no):", end=" ")
            confirm = input().strip().lower()
            if confirm == "yes":
                cleanup_temp_files(host, port, ssh_key, execute=True)
            else:
                print("Cancelled.")
        elif choice == "5":
            cleanup_cache(host, port, ssh_key, execute=False)
        elif choice == "6":
            print("\n⚠️  This will DELETE cache. Continue? (yes/no):", end=" ")
            confirm = input().strip().lower()
            if confirm == "yes":
                cleanup_cache(host, port, ssh_key, execute=True)
            else:
                print("Cancelled.")
        elif choice == "7":
            print("\n⚠️  This will perform FULL CLEANUP. Continue? (yes/no):", end=" ")
            confirm = input().strip().lower()
            if confirm == "yes":
                cleanup_temp_files(host, port, ssh_key, execute=True)
                cleanup_cache(host, port, ssh_key, execute=True)
                print("\n✅ Full cleanup complete!")
                show_disk_usage(host, port, ssh_key)
            else:
                print("Cancelled.")
        elif choice == "8":
            fp8, gguf = check_comfyui_model(host, port, ssh_key)
            show_recommendations(fp8, gguf)
        elif choice == "9":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please enter 1-9.")

        input("\nPress Enter to continue...")


def main():
    """Main execution."""
    print_header("ComfyUI Disk Space Fix Tool")
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get connection details
    host, port, ssh_key = get_runpod_connection()

    if not host or not port:
        print("\n⚠️  Could not auto-detect RunPod connection from runpod_config.py")
        print("\nPlease enter connection details manually:")
        host = input("SSH Host: ").strip()
        port = input("SSH Port: ").strip()
        ssh_key_input = input("SSH Key Path (or press Enter to skip): ").strip()
        ssh_key = ssh_key_input if ssh_key_input else None

    print(f"\n📡 Connecting to: {host}:{port}")

    # Test connection
    print("Testing connection...", end=" ")
    stdout, stderr, rc = execute_remote_command(host, port, "echo 'OK'", ssh_key)

    if rc == 0 and "OK" in stdout:
        print("✅ Connected!\n")
    else:
        print(f"❌ Failed!\nError: {stderr}")
        print("\nPlease check:")
        print("1. RunPod pod is running")
        print("2. SSH host and port are correct")
        print("3. SSH key is valid")
        sys.exit(1)

    # Run diagnostics
    show_disk_usage(host, port, ssh_key)
    fp8_exists, gguf_partial = check_comfyui_model(host, port, ssh_key)
    temp_count = count_temp_files(host, port, ssh_key)

    # Show recommendations
    show_recommendations(fp8_exists, gguf_partial)

    # Interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("\n🤖 AUTO MODE: Running automatic cleanup...")
        cleanup_temp_files(host, port, ssh_key, execute=True)
        cleanup_cache(host, port, ssh_key, execute=True)
        show_disk_usage(host, port, ssh_key)
    else:
        print("\n" + "=" * 80)
        print("Enter interactive mode? (y/n):", end=" ")
        choice = input().strip().lower()
        if choice == 'y':
            interactive_menu(host, port, ssh_key)
        else:
            print("\nUse --auto flag for automatic cleanup, or run again for interactive mode.")

    print_header("Summary")
    print("""
Tools available in this directory:
  - check_disk_space.py         : Detailed disk analysis
  - cleanup_comfyui_space.py    : Standalone cleanup tool
  - remote_cleanup.py            : Remote execution wrapper
  - fix_comfyui_space.py         : This tool (interactive)
  - DISK_SPACE_RESOLUTION.md     : Complete guide
  - COMFYUI_ERROR_SUMMARY.md     : Error analysis

For automatic cleanup:
  python fix_comfyui_space.py --auto

For full documentation:
  See DISK_SPACE_RESOLUTION.md
""")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
Immediate cleanup script for RunPod.
Uses paramiko for better SSH handling.
"""

import subprocess
import sys
import time

# SSH connection details
SSH_HOST = "ssh.runpod.io"
SSH_USER = "im5qj03lqzxugv-64410c77"
SSH_KEY = "~/.ssh/id_ed25519_runpod"

def run_ssh_command(command):
    """Execute SSH command and return output."""
    ssh_cmd = [
        "ssh",
        "-i", SSH_KEY.replace("~", "C:/Users/default.DESKTOP-A36S57H"),
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        f"{SSH_USER}@{SSH_HOST}",
        command
    ]

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        # Filter out the PTY error message
        output = result.stdout + result.stderr
        lines = [line for line in output.split('\n') if 'PTY' not in line and line.strip()]
        return '\n'.join(lines)
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 80)
    print("RunPod Disk Cleanup - Immediate Action")
    print("=" * 80)

    # Step 1: Check current disk usage
    print("\n1. Checking current disk usage...")
    output = run_ssh_command("df -h /workspace | tail -n 1")
    print(output)

    # Step 2: Find temporary files
    print("\n2. Finding temporary files...")
    temp_part = run_ssh_command("find /workspace/ComfyUI -name '*.part' 2>/dev/null | wc -l")
    temp_tmp = run_ssh_command("find /workspace/ComfyUI -name '*.tmp' 2>/dev/null | wc -l")
    print(f"   *.part files: {temp_part}")
    print(f"   *.tmp files: {temp_tmp}")

    # Step 3: Find incomplete GGUF download
    print("\n3. Checking for incomplete GGUF download...")
    gguf_files = run_ssh_command("find /workspace/ComfyUI/models -name '*Qwen*.gguf*' -o -name '*Qwen*.part' 2>/dev/null")
    if gguf_files:
        print("   Found:")
        for line in gguf_files.split('\n'):
            if line.strip():
                size = run_ssh_command(f"ls -lh '{line}' 2>/dev/null | awk '{{print $5}}'")
                print(f"   - {line} ({size})")
    else:
        print("   No GGUF files found")

    # Step 4: Check cache size
    print("\n4. Checking ComfyUI cache...")
    cache_size = run_ssh_command("du -sh /workspace/ComfyUI/user/default/ComfyUI-Manager/cache 2>/dev/null")
    print(f"   {cache_size}")

    # Step 5: Confirm cleanup
    print("\n" + "=" * 80)
    print("CLEANUP ACTIONS")
    print("=" * 80)
    print("""
This will:
1. Remove all *.part files (incomplete downloads)
2. Remove all *.tmp and *.temp files
3. Clear ComfyUI-Manager cache
4. Remove incomplete GGUF downloads

Expected space freed: 20-30GB

Continue? (yes/no): """, end="")

    confirm = input().strip().lower()
    if confirm != 'yes':
        print("\nCleanup cancelled.")
        return

    # Step 6: Execute cleanup
    print("\n" + "=" * 80)
    print("EXECUTING CLEANUP")
    print("=" * 80)

    print("\n1. Removing *.part files...")
    result = run_ssh_command("find /workspace/ComfyUI -name '*.part' -delete 2>/dev/null && echo 'Done'")
    print(f"   {result}")

    print("\n2. Removing *.tmp files...")
    result = run_ssh_command("find /workspace/ComfyUI -name '*.tmp' -delete 2>/dev/null && echo 'Done'")
    print(f"   {result}")

    print("\n3. Removing *.temp files...")
    result = run_ssh_command("find /workspace/ComfyUI -name '*.temp' -delete 2>/dev/null && echo 'Done'")
    print(f"   {result}")

    print("\n4. Clearing ComfyUI cache...")
    result = run_ssh_command("rm -rf /workspace/ComfyUI/user/default/ComfyUI-Manager/cache/* 2>/dev/null && echo 'Done'")
    print(f"   {result}")

    print("\n5. Removing incomplete GGUF downloads...")
    result = run_ssh_command("find /workspace/ComfyUI/models -name '*Qwen*Image*Edit*.gguf*' -delete 2>/dev/null && echo 'Done'")
    print(f"   {result}")

    # Step 7: Check final disk usage
    print("\n" + "=" * 80)
    print("FINAL DISK USAGE")
    print("=" * 80)
    time.sleep(2)  # Give filesystem time to update

    output = run_ssh_command("df -h /workspace")
    print(output)

    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Verify disk usage is now below 80%")
    print("2. Run: python download_workflow_models.py")
    print("3. Choose option 1 to download missing models")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCleanup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

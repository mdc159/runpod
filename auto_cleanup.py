#!/usr/bin/env python3
"""
Automatic cleanup script for RunPod - No user interaction required.
"""

import subprocess
import sys
import time

# SSH connection details
SSH_HOST = "ssh.runpod.io"
SSH_USER = "im5qj03lqzxugv-64410c77"
SSH_KEY_PATH = "C:/Users/default.DESKTOP-A36S57H/.ssh/id_ed25519_runpod"

def run_ssh(cmd):
    """Execute SSH command and return output."""
    ssh_cmd = [
        "ssh", "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        f"{SSH_USER}@{SSH_HOST}",
        cmd
    ]

    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
    output = result.stdout + result.stderr
    # Filter out PTY warnings
    return '\n'.join([l for l in output.split('\n') if 'PTY' not in l and l.strip()])

print("=" * 80)
print("RUNPOD AUTOMATIC CLEANUP")
print("=" * 80)

print("\n[1/7] Checking disk usage...")
disk = run_ssh("df -h /workspace | tail -n 1")
print(f"   {disk}")

print("\n[2/7] Counting temp files...")
part_count = run_ssh("find /workspace/ComfyUI -name '*.part' 2>/dev/null | wc -l")
tmp_count = run_ssh("find /workspace/ComfyUI -name '*.tmp' 2>/dev/null | wc -l")
print(f"   *.part files: {part_count.strip()}")
print(f"   *.tmp files: {tmp_count.strip()}")

print("\n[3/7] Removing *.part files...")
run_ssh("find /workspace/ComfyUI -name '*.part' -delete 2>/dev/null")
print("   ✓ Done")

print("\n[4/7] Removing *.tmp files...")
run_ssh("find /workspace/ComfyUI -name '*.tmp' -delete 2>/dev/null")
print("   ✓ Done")

print("\n[5/7] Removing *.temp files...")
run_ssh("find /workspace/ComfyUI -name '*.temp' -delete 2>/dev/null")
print("   ✓ Done")

print("\n[6/7] Clearing ComfyUI cache...")
run_ssh("rm -rf /workspace/ComfyUI/user/default/ComfyUI-Manager/cache/* 2>/dev/null")
print("   ✓ Done")

print("\n[7/7] Checking final disk usage...")
time.sleep(2)
disk_after = run_ssh("df -h /workspace | tail -n 1")
print(f"   {disk_after}")

print("\n" + "=" * 80)
print("✓ CLEANUP COMPLETE!")
print("=" * 80)
print("\nNext step: python download_workflow_models.py")

#!/usr/bin/env python3
"""
ComfyUI Space Cleanup Tool for RunPod
Safely removes temporary files and provides options for cleanup.
"""

import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime


def run_command(cmd, dry_run=True):
    """Execute a command with dry-run support."""
    if dry_run:
        print(f"[DRY RUN] Would execute: {cmd}")
        return ""
    else:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            print(f"[EXECUTED] {cmd}")
            if result.returncode != 0:
                print(f"[ERROR] {result.stderr}")
            return result.stdout.strip()
        except Exception as e:
            print(f"[ERROR] {e}")
            return ""


def cleanup_temporary_files(base_path="/workspace/ComfyUI", dry_run=True):
    """Remove temporary download files."""
    print("\n" + "=" * 80)
    print("CLEANING TEMPORARY FILES")
    print("=" * 80)

    patterns = [
        "*.part",
        "*.tmp",
        "*.temp",
        "*_temp_*"
    ]

    total_freed = 0

    for pattern in patterns:
        print(f"\nSearching for: {pattern}")

        # Find and display files
        find_cmd = f"find {base_path} -type f -name '{pattern}' -exec ls -lh {{}} \\; 2>/dev/null"
        result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)

        if result.stdout.strip():
            print(result.stdout)

            # Delete files
            delete_cmd = f"find {base_path} -type f -name '{pattern}' -delete"
            run_command(delete_cmd, dry_run)
        else:
            print(f"No files matching {pattern} found.")

    print()


def cleanup_comfyui_cache(dry_run=True):
    """Clear ComfyUI-Manager cache."""
    print("\n" + "=" * 80)
    print("CLEANING COMFYUI-MANAGER CACHE")
    print("=" * 80)

    cache_path = "/workspace/ComfyUI/user/default/ComfyUI-Manager/cache"

    # Check if path exists
    if os.path.exists(cache_path):
        # Get size before
        size_cmd = f"du -sh {cache_path}"
        result = subprocess.run(size_cmd, shell=True, capture_output=True, text=True)
        print(f"Current cache size: {result.stdout.strip()}")

        # Remove cache contents
        cmd = f"rm -rf {cache_path}/*"
        run_command(cmd, dry_run)
    else:
        print(f"Cache path does not exist: {cache_path}")

    print()


def list_large_models(base_path="/workspace/ComfyUI/models", min_size_gb=5):
    """List large model files for review."""
    print("\n" + "=" * 80)
    print(f"LARGE MODEL FILES (>{min_size_gb}GB)")
    print("=" * 80)

    cmd = f"find {base_path} -type f -size +{min_size_gb}G -exec ls -lh {{}} \\; 2>/dev/null | awk '{{print $5, $9}}' | sort -hr"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.stdout.strip():
        print(result.stdout)
        print("\nReview these files and manually delete any you don't need.")
    else:
        print(f"No model files larger than {min_size_gb}GB found.")

    print()


def check_incomplete_downloads(base_path="/workspace/ComfyUI/models"):
    """Find incomplete or failed downloads."""
    print("\n" + "=" * 80)
    print("CHECKING FOR INCOMPLETE DOWNLOADS")
    print("=" * 80)

    # Check for .part files (incomplete downloads)
    cmd = f"find {base_path} -type f -name '*.part' -o -name '*.download' 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.stdout.strip():
        print("Found incomplete downloads:")
        print(result.stdout)

        # Get detailed info
        for line in result.stdout.strip().split('\n'):
            if line:
                size_cmd = f"ls -lh '{line}'"
                size_result = subprocess.run(size_cmd, shell=True, capture_output=True, text=True)
                print(size_result.stdout)
    else:
        print("No incomplete downloads found.")

    print()


def analyze_output_folder(base_path="/workspace/ComfyUI/output"):
    """Analyze output folder."""
    print("\n" + "=" * 80)
    print("OUTPUT FOLDER ANALYSIS")
    print("=" * 80)

    if not os.path.exists(base_path):
        print(f"Output path does not exist: {base_path}")
        return

    # Get total size
    size_cmd = f"du -sh {base_path}"
    result = subprocess.run(size_cmd, shell=True, capture_output=True, text=True)
    print(f"Total output size: {result.stdout.strip()}")

    # Count files
    count_cmd = f"find {base_path} -type f | wc -l"
    result = subprocess.run(count_cmd, shell=True, capture_output=True, text=True)
    print(f"Total files: {result.stdout.strip()}")

    print("\nTo clear output folder (CAUTION - backup first if needed):")
    print(f"  rm -rf {base_path}/*")

    print()


def interactive_cleanup():
    """Interactive cleanup menu."""
    print("\n" + "=" * 80)
    print("INTERACTIVE CLEANUP")
    print("=" * 80)
    print("""
This script will help you free up space on your RunPod instance.

Options:
1. Dry run (recommended first) - shows what would be deleted
2. Execute cleanup - actually deletes files
3. Exit

Choose wisely!
""")


def main():
    """Main execution."""
    print(f"\n{'=' * 80}")
    print(f"ComfyUI Space Cleanup Tool")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")

    # Check if we're in dry-run mode
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        dry_run = False
        print("⚠️  EXECUTE MODE - Files will be permanently deleted!")
        print("Press Ctrl+C within 5 seconds to cancel...\n")
        import time
        time.sleep(5)
    else:
        print("🔍 DRY RUN MODE - No files will be deleted\n")
        print("Run with --execute flag to actually delete files\n")

    # Run cleanup operations
    cleanup_temporary_files(dry_run=dry_run)
    cleanup_comfyui_cache(dry_run=dry_run)
    check_incomplete_downloads()
    list_large_models()
    analyze_output_folder()

    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print("""
Additional manual cleanup options:

1. Review and remove unused models from /workspace/ComfyUI/models
2. Clear output folder if images are not needed
3. Check for duplicate model files
4. Remove old custom nodes you're not using

To see current disk usage:
  df -h /workspace

To find largest files:
  du -ah /workspace/ComfyUI | sort -rh | head -n 50
""")

    if dry_run:
        print("\n⚠️  This was a DRY RUN - no files were deleted.")
        print("Run with --execute flag to actually clean up files.")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

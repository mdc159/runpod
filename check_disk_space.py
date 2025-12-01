#!/usr/bin/env python3
"""
Disk Space Diagnostic Tool for RunPod ComfyUI
Analyzes disk usage and identifies large files that can be cleaned up.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime


def run_command(cmd):
    """Execute a command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def get_disk_usage():
    """Get overall disk usage information."""
    print("=" * 80)
    print("DISK USAGE SUMMARY")
    print("=" * 80)
    output = run_command("df -h /workspace")
    print(output)
    print()


def get_directory_sizes(base_path="/workspace/ComfyUI"):
    """Get sizes of main directories."""
    print("=" * 80)
    print("DIRECTORY SIZES IN COMFYUI")
    print("=" * 80)

    directories = [
        "models",
        "input",
        "output",
        "custom_nodes",
        "temp",
        "user"
    ]

    for dir_name in directories:
        dir_path = f"{base_path}/{dir_name}"
        size = run_command(f"du -sh {dir_path} 2>/dev/null || echo 'N/A'")
        print(f"{dir_name:20s}: {size}")
    print()


def get_model_subdirectory_sizes(base_path="/workspace/ComfyUI/models"):
    """Get sizes of model subdirectories."""
    print("=" * 80)
    print("MODEL SUBDIRECTORY SIZES")
    print("=" * 80)

    # Get all subdirectories
    output = run_command(f"du -h --max-depth=1 {base_path} 2>/dev/null | sort -hr")
    print(output)
    print()


def find_large_files(base_path="/workspace/ComfyUI", min_size_mb=1000):
    """Find files larger than specified size."""
    print("=" * 80)
    print(f"FILES LARGER THAN {min_size_mb}MB")
    print("=" * 80)

    # Find files larger than min_size_mb
    cmd = f"find {base_path} -type f -size +{min_size_mb}M -exec ls -lh {{}} \\; 2>/dev/null | awk '{{print $5, $9}}' | sort -hr"
    output = run_command(cmd)

    if output and not output.startswith("Error"):
        print(output)
    else:
        print(f"No files larger than {min_size_mb}MB found or error occurred.")
    print()


def find_temp_files(base_path="/workspace/ComfyUI"):
    """Find temporary and cache files."""
    print("=" * 80)
    print("TEMPORARY AND CACHE FILES")
    print("=" * 80)

    patterns = [
        "*.tmp",
        "*.temp",
        "*.part",
        "*_temp_*"
    ]

    for pattern in patterns:
        cmd = f"find {base_path} -type f -name '{pattern}' -exec ls -lh {{}} \\; 2>/dev/null | awk '{{print $5, $9}}'"
        output = run_command(cmd)
        if output and not output.startswith("Error") and output.strip():
            print(f"\nPattern: {pattern}")
            print(output)
    print()


def check_output_folder(base_path="/workspace/ComfyUI/output"):
    """Check output folder for old files."""
    print("=" * 80)
    print("OUTPUT FOLDER ANALYSIS")
    print("=" * 80)

    # Count files
    file_count = run_command(f"find {base_path} -type f 2>/dev/null | wc -l")
    print(f"Total files in output: {file_count}")

    # Total size
    total_size = run_command(f"du -sh {base_path} 2>/dev/null")
    print(f"Total size: {total_size}")

    # Files by extension
    print("\nFiles by extension:")
    cmd = f"find {base_path} -type f 2>/dev/null | sed 's/.*\\.//' | sort | uniq -c | sort -rn | head -20"
    output = run_command(cmd)
    print(output)
    print()


def generate_cleanup_recommendations():
    """Generate cleanup recommendations."""
    print("=" * 80)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. SAFE TO DELETE:
   - Temporary download files (*.part, *.tmp, *_temp_*)
   - Old output files (if not needed)
   - Cached files in ComfyUI-Manager cache

2. REVIEW BEFORE DELETING:
   - Duplicate or unused models
   - Large model files you're not using
   - Old workflow outputs

3. COMMANDS TO FREE SPACE:

   # Remove temporary files
   find /workspace/ComfyUI -type f -name "*.part" -delete
   find /workspace/ComfyUI -type f -name "*.tmp" -delete
   find /workspace/ComfyUI -type f -name "*_temp_*" -delete

   # Clear output folder (BE CAREFUL - backup first if needed)
   # rm -rf /workspace/ComfyUI/output/*

   # Clear ComfyUI-Manager cache
   rm -rf /workspace/ComfyUI/user/default/ComfyUI-Manager/cache/*

   # Remove specific large model if not needed (example)
   # rm /workspace/ComfyUI/models/diffusion_models/qwen-image-edit/*.safetensors

4. CHECK FOR INCOMPLETE DOWNLOADS:
   The error occurred while downloading Qwen-Image-Edit-2509-Q5_K_M.gguf
   Check for partial files in the gguf directory.
""")
    print()


def main():
    """Main execution."""
    print(f"\n{'=' * 80}")
    print(f"RunPod ComfyUI Disk Space Analysis")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")

    get_disk_usage()
    get_directory_sizes()
    get_model_subdirectory_sizes()
    find_large_files(min_size_mb=1000)
    find_temp_files()
    check_output_folder()
    generate_cleanup_recommendations()

    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

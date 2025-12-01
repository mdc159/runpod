# ComfyUI Disk Quota Exceeded - Resolution Guide

## Problem Summary

Your ComfyUI instance on RunPod ran out of disk space while downloading the Qwen-Image-Edit-2509-Q5_K_M.gguf model (14.9GB). The error `OSError: [Errno 122] Disk quota exceeded` occurred at 64% completion (~9.5GB downloaded).

## Immediate Actions

### 1. Diagnose Disk Usage

First, check your current disk usage:

```bash
# Connect to your RunPod instance via SSH
ssh root@<your-runpod-id>.runpod.io -p <port>

# Check overall disk usage
df -h /workspace

# Check ComfyUI directory size
du -sh /workspace/ComfyUI

# Check model directory sizes
du -h --max-depth=1 /workspace/ComfyUI/models | sort -hr
```

Or use the diagnostic script:

```bash
# Copy the script to your RunPod instance
scp check_disk_space.py root@<your-runpod-id>.runpod.io:/workspace/

# Run it
ssh root@<your-runpod-id>.runpod.io "cd /workspace && python check_disk_space.py"
```

### 2. Clean Up Space

#### Option A: Safe Automatic Cleanup (Recommended)

```bash
# Copy cleanup script to RunPod
scp cleanup_comfyui_space.py root@<your-runpod-id>.runpod.io:/workspace/

# Dry run first (see what would be deleted)
ssh root@<your-runpod-id>.runpod.io "cd /workspace && python cleanup_comfyui_space.py"

# Execute cleanup if satisfied with dry run
ssh root@<your-runpod-id>.runpod.io "cd /workspace && python cleanup_comfyui_space.py --execute"
```

#### Option B: Manual Cleanup

```bash
# Remove temporary download files
find /workspace/ComfyUI -type f -name "*.part" -delete
find /workspace/ComfyUI -type f -name "*.tmp" -delete
find /workspace/ComfyUI -type f -name "*.temp" -delete

# Remove the incomplete GGUF download
rm -f /workspace/ComfyUI/models/gguf/Qwen-Image-Edit-2509-Q5_K_M.gguf.part
rm -f /workspace/ComfyUI/models/gguf/Qwen-Image-Edit-2509-Q5_K_M.gguf

# Clear ComfyUI-Manager cache
rm -rf /workspace/ComfyUI/user/default/ComfyUI-Manager/cache/*

# Clear old outputs (if not needed)
rm -rf /workspace/ComfyUI/output/*

# Clear temp directory
rm -rf /workspace/ComfyUI/temp/*
```

### 3. Find Large Files to Remove

```bash
# Find files larger than 5GB
find /workspace/ComfyUI -type f -size +5G -exec ls -lh {} \; | awk '{print $5, $9}' | sort -hr

# Find files larger than 1GB
find /workspace/ComfyUI -type f -size +1G -exec ls -lh {} \; | awk '{print $5, $9}' | sort -hr

# Check model subdirectories
du -h --max-depth=2 /workspace/ComfyUI/models | sort -hr | head -20
```

## Long-term Solutions

### 1. Choose Smaller Model Variants

The model you were downloading is **14.9GB**. Consider these alternatives:

- **Q4_K_M** variant: Smaller, faster, slight quality trade-off
- **Q5_0** variant: Good balance between size and quality
- **FP8** variant: Already downloaded (20.4GB) - you may want to use this instead

**Note**: You already have the FP8 model (`qwen_image_edit_2509_fp8_e4m3fn.safetensors` - 20.4GB) downloaded successfully!

### 2. Upgrade RunPod Storage

If you frequently work with large models:

1. Go to RunPod dashboard
2. Stop your pod
3. Increase container disk size
4. Restart pod

### 3. Use Model Management Best Practices

```bash
# Before downloading, check available space
df -h /workspace

# Calculate if you have enough space:
# - Current download: 14.9GB
# - Need ~20GB free (for temp files during download)
# - Recommended: 30GB free for safety

# Remove models you're not using
cd /workspace/ComfyUI/models
ls -lh diffusion_models/
ls -lh checkpoints/
ls -lh loras/
```

### 4. Organize Models

Create a model inventory:

```bash
# List all models with sizes
find /workspace/ComfyUI/models -type f \( -name "*.safetensors" -o -name "*.gguf" -o -name "*.pt" -o -name "*.ckpt" \) -exec ls -lh {} \; | awk '{print $5, $9}' | sort -rh > /workspace/model_inventory.txt

# Review the inventory
cat /workspace/model_inventory.txt
```

## Specific Fix for Your Situation

Based on the logs, you already downloaded the FP8 model successfully:

```
Install model 'Qwen-Image-Edit 2509 Diffusion Model (fp8_e4m3fn)'
from 'https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/...'
into '/workspace/ComfyUI/models/diffusion_models/qwen-image-edit/qwen_image_edit_2509_fp8_e4m3fn.safetensors'

100%|██████████| 20.4G/20.4G [01:36<00:00, 211MB/s]
```

**Recommendation**: Use the FP8 model instead of downloading the GGUF variant. The FP8 version is already optimized for inference and is working.

### If you absolutely need the GGUF model:

1. Delete the FP8 model (free 20.4GB):
   ```bash
   rm /workspace/ComfyUI/models/diffusion_models/qwen-image-edit/qwen_image_edit_2509_fp8_e4m3fn.safetensors
   ```

2. Clear any partial downloads:
   ```bash
   find /workspace/ComfyUI/models -name "*Qwen-Image-Edit-2509*.part" -delete
   ```

3. Verify you have >20GB free:
   ```bash
   df -h /workspace
   ```

4. Retry the download

## Prevention Checklist

Before downloading large models:

- [ ] Check available disk space: `df -h /workspace`
- [ ] Estimate needed space: Model size × 1.5
- [ ] Clean up old outputs/temp files
- [ ] Remove unused models
- [ ] Consider smaller quantized variants
- [ ] Use model manager to track downloads

## Quick Reference Commands

```bash
# Check disk usage
df -h /workspace

# Quick cleanup
rm -rf /workspace/ComfyUI/output/*
rm -rf /workspace/ComfyUI/temp/*
find /workspace/ComfyUI -name "*.part" -delete
find /workspace/ComfyUI -name "*.tmp" -delete

# Find space hogs
du -ah /workspace/ComfyUI | sort -rh | head -n 30

# Monitor disk during download
watch -n 5 'df -h /workspace'
```

## Using the Python Scripts

### From Your Local Machine (Windows)

```powershell
# Check disk space remotely
python file_transfer.py  # Use your existing transfer script
# Then SSH in and run: python /workspace/check_disk_space.py

# Or create a new script to automate this
```

### From RunPod SSH

```bash
# Upload scripts
scp check_disk_space.py cleanup_comfyui_space.py root@<runpod-ip>:/workspace/

# SSH in
ssh root@<runpod-ip>

# Run diagnostic
python /workspace/check_disk_space.py > /workspace/disk_report.txt

# Run cleanup (dry run)
python /workspace/cleanup_comfyui_space.py

# Execute cleanup
python /workspace/cleanup_comfyui_space.py --execute
```

## Summary

1. **Immediate**: Clean up temporary files and old outputs
2. **Short-term**: Use the FP8 model you already have
3. **Long-term**: Upgrade storage or manage models better
4. **Prevention**: Always check space before large downloads

The scripts provided will help you:
- Diagnose exactly where space is being used
- Safely clean up temporary and cache files
- Identify large models to review
- Prevent future quota issues

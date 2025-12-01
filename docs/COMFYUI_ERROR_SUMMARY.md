# ComfyUI Disk Quota Error - Complete Analysis & Solution

## Error Summary

**Error Type**: `OSError: [Errno 122] Disk quota exceeded`
**Node**: URL Downloader (Node ID: 1363)
**Context**: Downloading Qwen-Image-Edit-2509-Q5_K_M.gguf (14.9GB)
**Progress at failure**: 64% complete (~9.5GB downloaded)
**Date**: 2025-10-18 21:45:07

## Root Cause

Your RunPod container ran out of disk space while downloading a large model file. The download was interrupted at 64% completion, leaving a partial file that's consuming ~9.5GB of space.

## Key Observations

### What Worked Previously

✅ Successfully downloaded FP8 model (20.4GB) at 21:38:40:

```
Install model 'Qwen-Image-Edit 2509 Diffusion Model (fp8_e4m3fn)'
100%|██████████| 20.4G/20.4G [01:36<00:00, 211MB/s]
```

### What Failed

❌ GGUF model download (14.9GB) at 21:45:07:

```
Qwen-Image-Edit-2509-Q5_K_M.gguf: 64%|██████▍ | 9.53G/14.9G
OSError: [Errno 122] Disk quota exceeded
```

### Current System State

- **Platform**: Linux (RunPod)
- **ComfyUI Version**: 0.3.65
- **Python**: 3.11.11
- **GPU**: NVIDIA GeForce RTX 5090 (33GB VRAM)
- **Working Directory**: /workspace/ComfyUI

## Immediate Solution

### Option 1: Use the FP8 Model (Recommended)

You already have a working model! The FP8 version is suitable for your use case:

**Location**: `/workspace/ComfyUI/models/diffusion_models/qwen-image-edit/qwen_image_edit_2509_fp8_e4m3fn.safetensors`

**Action**: Update your ComfyUI workflow to use this model instead of trying to download the GGUF version.

### Option 2: Clean Up and Retry GGUF Download

If you absolutely need the GGUF model:

1. **Free up space** (choose appropriate actions):

   ```bash
   # Remove the incomplete GGUF download
   rm /workspace/ComfyUI/models/gguf/Qwen-Image-Edit-2509-Q5_K_M.gguf*

   # Remove temporary files
   find /workspace/ComfyUI -name "*.part" -delete
   find /workspace/ComfyUI -name "*.tmp" -delete

   # Clear old outputs
   rm -rf /workspace/ComfyUI/output/*

   # Clear cache
   rm -rf /workspace/ComfyUI/user/default/ComfyUI-Manager/cache/*

   # If needed, remove the FP8 model to free 20.4GB
   rm /workspace/ComfyUI/models/diffusion_models/qwen-image-edit/qwen_image_edit_2509_fp8_e4m3fn.safetensors
   ```

2. **Verify space**:

   ```bash
   df -h /workspace
   # Should show at least 20GB free
   ```

3. **Retry download** in ComfyUI

## Tools Provided

I've created several tools to help you manage this situation:

### 1. [check_disk_space.py](check_disk_space.py)

**Purpose**: Comprehensive disk usage analysis
**Usage**:

```bash
# From local machine
scp check_disk_space.py root@<runpod-host>:/workspace/
ssh root@<runpod-host> "python /workspace/check_disk_space.py"

# Or directly on RunPod
python /workspace/check_disk_space.py
```

**Output**: Shows disk usage, directory sizes, large files, temp files

### 2. [cleanup_comfyui_space.py](cleanup_comfyui_space.py)

**Purpose**: Safe cleanup of temporary and cache files
**Usage**:

```bash
# Dry run (see what would be deleted)
python cleanup_comfyui_space.py

# Execute cleanup
python cleanup_comfyui_space.py --execute
```

**Actions**:

- Removes *.part,*.tmp, *.temp files
- Clears ComfyUI-Manager cache
- Lists large models for review
- Analyzes output folder

### 3. [remote_cleanup.py](remote_cleanup.py)

**Purpose**: Execute cleanup from your local machine
**Usage**:

```bash
# Dry run
python remote_cleanup.py

# Execute
python remote_cleanup.py --execute
```

**Features**:

- Uses your existing runpod_config.py
- SSH-based remote execution
- No need to manually SSH in

### 4. [DISK_SPACE_RESOLUTION.md](DISK_SPACE_RESOLUTION.md)

**Purpose**: Complete troubleshooting guide
**Contains**:

- Step-by-step resolution
- Manual commands
- Prevention strategies
- Best practices

## Quick Start Guide

### From Your Windows Machine

```powershell
# 1. Run remote diagnostic
python remote_cleanup.py

# 2. Review the output to see space usage

# 3. Execute cleanup (if satisfied with dry run)
python remote_cleanup.py --execute

# 4. Check if space is now available
ssh root@<your-runpod> "df -h /workspace"
```

### From RunPod SSH

```bash
# 1. SSH into your pod
ssh root@<your-runpod-host> -p <port>

# 2. Check disk usage
df -h /workspace

# 3. Quick cleanup
rm -rf /workspace/ComfyUI/output/*
find /workspace/ComfyUI -name "*.part" -delete
find /workspace/ComfyUI -name "*.tmp" -delete

# 4. Check space again
df -h /workspace
```

## Long-term Prevention

### 1. Monitor Disk Usage

Add this to your workflow:

```bash
# Before large downloads
df -h /workspace
```

### 2. Regular Cleanup

Schedule regular cleanup of:

- Output folder (images you don't need)
- Temporary files
- ComfyUI-Manager cache
- Unused models

### 3. Model Management

- Keep inventory of installed models
- Remove unused models
- Choose appropriate quantization (Q4, Q5, FP8)
- Consider model size before downloading

### 4. Increase Storage

If you regularly work with large models:

1. Stop your RunPod pod
2. Go to pod settings
3. Increase "Container Disk"
4. Restart pod

**Recommended**: 200GB+ for heavy ComfyUI usage

## Model Comparison

| Model | Size | Status | Notes |
|-------|------|--------|-------|
| FP8 (safetensors) | 20.4GB | ✅ Downloaded | Ready to use |
| Q5_K_M (gguf) | 14.9GB | ❌ Failed | 64% downloaded, incomplete |
| Q4_K_M (gguf) | ~11GB | - | Smaller alternative |
| Q5_0 (gguf) | ~13GB | - | Good balance |

**Recommendation**: Use the FP8 model you already have, or download a smaller quantized version if the GGUF format is required.

## Next Steps

1. **Immediate** (choose one):
   - Option A: Use the FP8 model already downloaded ✅ Recommended
   - Option B: Clean up space and retry GGUF download

2. **Short-term**:
   - Run `remote_cleanup.py` to diagnose and clean
   - Review large files and remove unused models
   - Clear output folder if images aren't needed

3. **Long-term**:
   - Consider upgrading RunPod storage
   - Implement regular cleanup routine
   - Keep model inventory
   - Monitor disk usage

## Support Scripts

All scripts are located in: `x:/GitHub/runpod/`

- `check_disk_space.py` - Disk usage diagnostic
- `cleanup_comfyui_space.py` - Automated cleanup
- `remote_cleanup.py` - Remote execution tool
- `DISK_SPACE_RESOLUTION.md` - Detailed guide
- `COMFYUI_ERROR_SUMMARY.md` - This file

## Additional Resources

- [ComfyUI Documentation](https://github.com/comfyanonymous/ComfyUI)
- [RunPod Documentation](https://docs.runpod.io/)
- [Model Quantization Guide](https://huggingface.co/docs/transformers/main/en/quantization)

## Questions?

If you need help with:

- Running the cleanup scripts
- Choosing which models to keep
- Upgrading RunPod storage
- Optimizing ComfyUI setup

Feel free to ask!

---

**Generated**: 2025-10-18
**Tools Version**: 1.0
**Status**: Ready for deployment

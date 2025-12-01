# Upgrade RunPod Storage - Quick Guide

## Why Upgrade?

- **Current**: ~100GB (93% full = ~7GB free)
- **Needed**: 150-200GB for comfortable ComfyUI usage with your workflow
- **Cost**: Very cheap (pennies per hour for additional storage)

## How to Upgrade Storage

### Step 1: Stop Your Pod

1. Go to [RunPod Console](https://www.runpod.io/console/pods)
2. Find your pod: `uncomfortable_black_cattle` (im5zj031szxugv)
3. Click **Stop** button

### Step 2: Edit Pod Configuration

1. Once stopped, click the **Edit** button
2. Find the **"Container Disk"** setting
3. Change from current size to **150GB** or **200GB**
   - 150GB: Good for most workflows
   - 200GB: Better if you plan to have many models

### Step 3: Restart Pod

1. Click **Save** to save the new configuration
2. Click **Start** to restart your pod
3. Wait for pod to come online (~1-2 minutes)

### Step 4: Verify New Space

1. Check the disk indicator in your RunPod dashboard
2. It should now show much lower usage percentage

## Cost Impact

Storage costs are minimal:
- **Additional 50GB**: ~$0.01-0.02/hour extra
- **Additional 100GB**: ~$0.02-0.04/hour extra

**Example**: If you run your pod 40 hours/month with +100GB storage:

- Extra cost: ~$0.80-1.60/month
- Total extra cost: **Less than $2/month**

## What This Gives You

With 150-200GB total storage:

✅ Room for all workflow models (~60-65GB)
✅ Space for outputs (~20-30GB)
✅ Temp files and cache (~10-20GB)
✅ Future model downloads
✅ No more "disk quota exceeded" errors
✅ No need to constantly delete files

## After Upgrading

Once you have more storage, you can:

```bash
# Download all workflow models without worry
python download_workflow_models.py
# Choose option 1
```

This will download ~28GB of missing models with plenty of room to spare.

## Alternative: Volume Storage

If you want persistent storage that survives pod restarts:

1. Create a **Network Volume** (separate from container disk)
2. Attach it to your pod
3. Store models there permanently
4. Costs more but data persists across pod sessions

**For your use case**: Just increasing container disk is simpler and cheaper.

## Summary

**Recommended Action**:
1. Stop pod
2. Increase Container Disk to **150GB** or **200GB**
3. Restart pod
4. Run `python download_workflow_models.py`
5. Done!

**Cost**: Less than $2/month extra
**Time**: 5 minutes to upgrade
**Benefit**: No more space issues!

---

**Ready to proceed?** Stop your pod and upgrade the storage, then we can download all your models hassle-free!

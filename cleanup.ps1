# RunPod Cleanup Script - PowerShell
# This script cleans up disk space on your RunPod instance

$SSH_KEY = "C:\Users\default.DESKTOP-A36S57H\.ssh\id_ed25519_runpod"
$SSH_USER = "im5qj03lqzxugv-64410c77"
$SSH_HOST = "ssh.runpod.io"

Write-Host "=" * 80
Write-Host "RUNPOD CLEANUP SCRIPT"
Write-Host "=" * 80

Write-Host "`n[Step 1] Checking current disk usage..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "df -h /workspace" 2>$null

Write-Host "`n[Step 2] Cleaning temporary files..."
Write-Host "   Removing *.part files..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "find /workspace/ComfyUI -name '*.part' -delete 2>/dev/null" 2>$null
Write-Host "   [OK]"

Write-Host "   Removing *.tmp files..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "find /workspace/ComfyUI -name '*.tmp' -delete 2>/dev/null" 2>$null
Write-Host "   [OK]"

Write-Host "   Removing *.temp files..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "find /workspace/ComfyUI -name '*.temp' -delete 2>/dev/null" 2>$null
Write-Host "   [OK]"

Write-Host "`n[Step 3] Clearing ComfyUI-Manager cache..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "rm -rf /workspace/ComfyUI/user/default/ComfyUI-Manager/cache/*" 2>$null
Write-Host "   [OK]"

Write-Host "`n[Step 4] Removing incomplete GGUF downloads..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "find /workspace/ComfyUI/models -name '*Qwen*Image*Edit*.gguf*' -delete 2>/dev/null" 2>$null
Write-Host "   [OK]"

Write-Host "`n[Step 5] Checking final disk usage..."
Start-Sleep -Seconds 2
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "df -h /workspace" 2>$null

Write-Host "`n" + "=" * 80
Write-Host "CLEANUP COMPLETE!"
Write-Host "=" * 80
Write-Host "`nNext step: Run 'python download_workflow_models.py'"

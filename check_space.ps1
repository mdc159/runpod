# Check what's using space on RunPod

$SSH_KEY = "C:\Users\default.DESKTOP-A36S57H\.ssh\id_ed25519_runpod"
$SSH_USER = "im5qj03lqzxugv-64410c77"
$SSH_HOST = "ssh.runpod.io"

Write-Host "Checking disk usage on RunPod...`n"

Write-Host "=== DISK USAGE ==="
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "df -h /workspace | tail -n 1" 2>$null

Write-Host "`n=== TOP DIRECTORIES ==="
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "du -h --max-depth=1 /workspace/ComfyUI 2>/dev/null | sort -hr | head -10" 2>$null

Write-Host "`n=== MODEL DIRECTORIES ==="
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "du -h --max-depth=1 /workspace/ComfyUI/models 2>/dev/null | sort -hr | head -15" 2>$null

Write-Host "`n=== LARGEST FILES >5GB ==="
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "find /workspace/ComfyUI -type f -size +5G -exec ls -lh {} \; 2>/dev/null | awk '{print `$5, `$9}' | sort -hr" 2>$null

Write-Host "`n=== OUTPUT FOLDER ==="
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "du -sh /workspace/ComfyUI/output 2>/dev/null" 2>$null

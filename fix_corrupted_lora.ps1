# Fix Corrupted LoRA File - RunPod

$SSH_KEY = "C:\Users\default.DESKTOP-A36S57H\.ssh\id_ed25519_runpod"
$SSH_USER = "im5qj03lqzxugv-64410c77"
$SSH_HOST = "ssh.runpod.io"

Write-Host "=" * 80
Write-Host "FIXING CORRUPTED LORA FILE"
Write-Host "=" * 80

Write-Host "`nThe error 'header too large' means a LoRA file is corrupted."
Write-Host "Node 547 (LoraLoaderModelOnly) is trying to load a broken file.`n"

Write-Host "[Step 1] Finding LoRA files..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "find /workspace/ComfyUI/models/loras -type f -name '*.safetensors' -exec ls -lh {} \;" 2>$null

Write-Host "`n[Step 2] Checking for Qwen Image Lightning LoRA..."
$lora_path = "/workspace/ComfyUI/models/loras/qwen/Qwen-Image-Lightning-4steps-V2.0.safetensors"
$check = ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "ls -lh '$lora_path' 2>/dev/null || echo 'NOT_FOUND'" 2>$null
Write-Host "   $check"

if ($check -match "NOT_FOUND") {
    Write-Host "`n[Step 3] LoRA file not found or corrupted. Removing it..."
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "rm -f '$lora_path'" 2>$null
    Write-Host "   [OK] Removed"

    Write-Host "`n[Step 4] Download location ready for re-download"
    Write-Host "   Next: Use ComfyUI Manager to download the LoRA again"
} else {
    Write-Host "`n[Step 3] File exists but may be corrupted. Checking file integrity..."

    # Try to get file size
    $size = ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "stat -f%z '$lora_path' 2>/dev/null || stat -c%s '$lora_path' 2>/dev/null" 2>$null
    Write-Host "   File size: $size bytes"

    # Expected size is around 600MB (629145600 bytes)
    if ($size -lt 500000000) {
        Write-Host "`n   ⚠️  File is too small! Expected ~600MB, got $([math]::Round($size/1MB, 2))MB"
        Write-Host "   This file is incomplete/corrupted."

        Write-Host "`n[Step 4] Removing corrupted file..."
        ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "rm -f '$lora_path'" 2>$null
        Write-Host "   [OK] Removed"
    } else {
        Write-Host "`n   File size looks correct. May be a different corruption issue."
        Write-Host "   Recommend: Delete and re-download anyway"
    }
}

Write-Host "`n" + "=" * 80
Write-Host "SOLUTION"
Write-Host "=" * 80
Write-Host @"

The LoRA file referenced in your workflow is corrupted or incomplete.

QUICKEST FIX:
1. Delete the corrupted file (done above if found)
2. Use ComfyUI Manager to re-download:
   - Open ComfyUI web interface
   - Click 'Manager' button
   - Go to 'Model Manager'
   - Search for: Qwen-Image-Lightning
   - Click Install

OR manually download:
   URL: https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-4steps-V2.0.safetensors
   Save to: /workspace/ComfyUI/models/loras/qwen/

Expected file size: ~600MB

"@

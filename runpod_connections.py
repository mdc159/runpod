"""
RunPod Multi-Connection Client
This script handles different types of RunPod connections:
1. S3 Storage (for file storage)
2. SSH Connection (for direct server access)
3. API Connection (for programmatic access)
"""

import os
import re
import subprocess
import boto3
import paramiko
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path

class RunPodConnections:
    """Handles multiple types of RunPod connections."""
    
    def __init__(self, env_file_path: str = ".env", verbose: bool = False):
        """Initialize with credentials from .env file."""
        self.credentials = self._load_credentials(env_file_path)
        self.s3_client = None
        self.ssh_client = None
        self.verbose = verbose
    
    def _load_credentials(self, env_file_path: str) -> Dict[str, str]:
        """Load credentials from the .env file (robust parsing)."""
        credentials: Dict[str, Any] = {}
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                lines = [ln.rstrip("\r\n") for ln in f]

            # Normalize k/v pairs of the form "key = value" or "key: value"
            alias_map = {
                'aws_access_key_id': ['aws_access_key_id', 'aws access key id', 'access_key', 'access key id'],
                'aws_secret_access_key': ['aws_secret_access_key', 'aws secret access key', 'secret_key', 'secret access key'],
                'bucket_name': ['bucket name', 'bucket', 's3 bucket', 's3_bucket'],
                'endpoint_url': ['endpoint url', 'endpoint-url', 'endpoint', 's3 endpoint', 's3 endpoint url'],
            }

            def canonical_key(raw_key: str) -> Optional[str]:
                key_norm = re.sub(r"[^a-z0-9]", " ", raw_key.lower()).strip()
                key_norm = re.sub(r"\s+", " ", key_norm)
                for canon, aliases in alias_map.items():
                    if key_norm == canon or key_norm in aliases:
                        return canon
                return None

            for raw in lines:
                line = raw.strip()
                if not line or line.startswith('#') or line.startswith('['):
                    continue
                # Split on first '=' or ':'
                if '=' in line:
                    key, value = line.split('=', 1)
                elif ':' in line:
                    key, value = line.split(':', 1)
                else:
                    key, value = None, None
                if key is None:
                    continue
                key = key.strip()
                value = value.strip()
                ckey = canonical_key(key)
                if ckey:
                    credentials[ckey] = value

            # Fallbacks: keep original exact keys if present
            credentials.setdefault('aws_access_key_id', '')
            credentials.setdefault('aws_secret_access_key', '')
            credentials.setdefault('bucket_name', '')
            credentials.setdefault('endpoint_url', '')

            # Extract SSH lines robustly
            for raw in lines:
                line = raw.strip()
                if not line.startswith('ssh '):
                    continue
                # Pattern 1: ssh user@host ...
                m1 = re.search(r"ssh\s+([^\s@]+)@([^\s]+)", line)
                if m1:
                    credentials['ssh_username'] = m1.group(1)
                    credentials['ssh_host'] = m1.group(2)
                # Pattern 2: -p PORT
                m2 = re.search(r"\s-p\s+(\d+)", line)
                if m2:
                    try:
                        credentials['ssh_port'] = int(m2.group(1))
                    except ValueError:
                        credentials['ssh_port'] = 22
                # If direct IP present (root@IP)
                m3 = re.search(r"ssh\s+root@([0-9.]+)", line)
                if m3:
                    credentials['ssh_ip'] = m3.group(1)
                    credentials.setdefault('ssh_port', 22)

        except FileNotFoundError:
            print(f"❌ Environment file '{env_file_path}' not found")
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")

        return credentials
    
    def get_s3_client(self):
        """Get S3 client for RunPod storage."""
        if self.s3_client is None:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.credentials['aws_access_key_id'],
                    aws_secret_access_key=self.credentials['aws_secret_access_key'],
                    endpoint_url=self.credentials['endpoint_url'],
                    region_name='us-ca-2'
                )
                print("[OK] S3 client initialized")
            except Exception as e:
                print(f"[ERROR] Error initializing S3 client: {e}")
                return None
        
        return self.s3_client
    
    def list_s3_files(self, prefix: str = "") -> List[str]:
        """List files in the S3 bucket."""
        s3 = self.get_s3_client()
        if not s3:
            return []
        
        try:
            response = s3.list_objects_v2(
                Bucket=self.credentials['bucket_name'],
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append(obj['Key'])
            
            return files
        except Exception as e:
            print(f"[ERROR] Error listing S3 files: {e}")
            return []
    
    def upload_to_s3(self, local_file_path: str, s3_key: str) -> bool:
        """Upload a file to S3."""
        s3 = self.get_s3_client()
        if not s3:
            return False
        
        try:
            s3.upload_file(local_file_path, self.credentials['bucket_name'], s3_key)
            print(f"[OK] Uploaded {local_file_path} to s3://{self.credentials['bucket_name']}/{s3_key}")
            return True
        except Exception as e:
            print(f"[ERROR] Error uploading to S3: {e}")
            return False
    
    def download_from_s3(self, s3_key: str, local_file_path: str) -> bool:
        """Download a file from S3."""
        s3 = self.get_s3_client()
        if not s3:
            return False
        
        try:
            s3.download_file(self.credentials['bucket_name'], s3_key, local_file_path)
            print(f"[OK] Downloaded s3://{self.credentials['bucket_name']}/{s3_key} to {local_file_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error downloading from S3: {e}")
            return False
    
    def _find_ssh_key(self, preferred_key: str = "~/.ssh/id_ed25519") -> Optional[str]:
        """Find an available SSH key."""
        ssh_dir = Path.home() / ".ssh"

        # Try preferred key first
        preferred = Path(os.path.expanduser(preferred_key))
        if preferred.exists():
            return str(preferred)

        # Search for common SSH key names
        if ssh_dir.exists():
            for key_name in ['id_ed25519', 'id_rsa', 'id_ecdsa']:
                key_path = ssh_dir / key_name
                if key_path.exists():
                    return str(key_path)

            # Look for any ed25519 or rsa keys
            for key_file in ssh_dir.glob('id_*'):
                if key_file.is_file() and not key_file.name.endswith('.pub'):
                    return str(key_file)

        return None

    def ssh_connect(self, key_path: str = "~/.ssh/id_ed25519_runpod") -> bool:
        """Connect via SSH to RunPod."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Find an available SSH key
            actual_key_path = self._find_ssh_key(key_path)
            if not actual_key_path:
                print("[ERROR] No SSH key found. Please create one with: ssh-keygen -t ed25519")
                return False

            if self.verbose:
                print(f"[INFO] Using SSH key: {actual_key_path}")

            # Try the main SSH endpoint first
            ssh_host = self.credentials.get('ssh_host', 'ssh.runpod.io')
            ssh_username = self.credentials.get('ssh_username', '')

            if ssh_username and ssh_host:
                self.ssh_client.connect(
                    ssh_host,
                    username=ssh_username,
                    key_filename=actual_key_path
                )
                print(f"[OK] Connected to {ssh_username}@{ssh_host}")
                return True

            # Try direct IP connection
            ssh_ip = self.credentials.get('ssh_ip', '')
            ssh_port = self.credentials.get('ssh_port', 22)

            if ssh_ip:
                self.ssh_client.connect(
                    ssh_ip,
                    port=ssh_port,
                    username='root',
                    key_filename=actual_key_path
                )
                print(f"[OK] Connected to root@{ssh_ip}:{ssh_port}")
                return True

            print("[ERROR] No valid SSH connection info found")
            return False

        except Exception as e:
            print(f"[ERROR] SSH connection failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def ssh_execute(self, command: str) -> tuple:
        """Execute a command via SSH."""
        if not self.ssh_client:
            if not self.ssh_connect():
                return None, "SSH connection failed"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output, error
        except Exception as e:
            return None, str(e)
    
    def ssh_upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file via SSH."""
        if not self.ssh_client:
            if not self.ssh_connect():
                return False
        
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            print(f"[OK] Uploaded {local_path} to {remote_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error uploading file via SSH: {e}")
            return False
    
    def ssh_download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file via SSH."""
        if not self.ssh_client:
            if not self.ssh_connect():
                return False
        
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            print(f"[OK] Downloaded {remote_path} to {local_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error downloading file via SSH: {e}")
            return False
    
    def close_ssh(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
            print("[OK] SSH connection closed")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about available connections."""
        s3_ok = all([
            bool(self.credentials.get('aws_access_key_id')),
            bool(self.credentials.get('aws_secret_access_key')),
            bool(self.credentials.get('bucket_name')),
            bool(self.credentials.get('endpoint_url')),
        ])
        return {
            's3_available': s3_ok,
            'ssh_available': bool(self.credentials.get('ssh_host') or self.credentials.get('ssh_ip')),
            'bucket_name': self.credentials.get('bucket_name', ''),
            'endpoint_url': self.credentials.get('endpoint_url', ''),
            'ssh_host': self.credentials.get('ssh_host', ''),
            'ssh_username': self.credentials.get('ssh_username', ''),
            'ssh_ip': self.credentials.get('ssh_ip', ''),
            'ssh_port': self.credentials.get('ssh_port', 22)
        }

def main():
    """Test all RunPod connections."""
    print("🚀 RunPod Multi-Connection Test")
    print("=" * 50)
    
    # Initialize connections
    runpod = RunPodConnections(verbose=True)
    
    # Show connection info
    info = runpod.get_connection_info()
    print("\n📊 Connection Information:")
    print(f"S3 Available: {'✅' if info['s3_available'] else '❌'}")
    print(f"SSH Available: {'✅' if info['ssh_available'] else '❌'}")
    print(f"Bucket: {info['bucket_name']}")
    print(f"SSH Host: {info['ssh_host'] or info['ssh_ip']}")
    # Optional verbose dump (redacted)
    try:
        if runpod.verbose:
            redacted = {
                'aws_access_key_id': '***' if runpod.credentials.get('aws_access_key_id') else '',
                'aws_secret_access_key': '***' if runpod.credentials.get('aws_secret_access_key') else '',
                'bucket_name': runpod.credentials.get('bucket_name', ''),
                'endpoint_url': runpod.credentials.get('endpoint_url', ''),
                'ssh_username': runpod.credentials.get('ssh_username', ''),
                'ssh_host': runpod.credentials.get('ssh_host', ''),
                'ssh_ip': runpod.credentials.get('ssh_ip', ''),
                'ssh_port': runpod.credentials.get('ssh_port', 22),
            }
            print("\n🔎 Parsed credentials (redacted):")
            for k, v in redacted.items():
                print(f"  {k}: {v}")
    except Exception:
        pass
    
    # Test S3 connection
    if info['s3_available']:
        print("\n🗄️  Testing S3 Connection...")
        files = runpod.list_s3_files()
        print(f"Found {len(files)} files in S3 bucket")
        if files:
            print("Sample files:")
            for file in files[:5]:  # Show first 5 files
                print(f"  - {file}")
    
    # Test SSH connection
    if info['ssh_available']:
        print("\n🔐 Testing SSH Connection...")
        if runpod.ssh_connect():
            # Test a simple command
            output, error = runpod.ssh_execute("pwd")
            if output:
                print(f"Current directory: {output.strip()}")
            
            # Test system info
            output, error = runpod.ssh_execute("uname -a")
            if output:
                print(f"System info: {output.strip()}")
            
            runpod.close_ssh()
        else:
            print("❌ SSH connection failed")
    
    print("\n🎉 Connection test completed!")

if __name__ == "__main__":
    main()


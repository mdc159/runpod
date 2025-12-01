"""
SSH Connection Diagnostic Tool for RunPod
"""

import os
import paramiko
from pathlib import Path

def find_ssh_key():
    """Find available SSH keys."""
    ssh_dir = Path.home() / ".ssh"
    keys_found = []

    if ssh_dir.exists():
        for key_file in ssh_dir.glob('id_*'):
            if key_file.is_file() and not key_file.name.endswith('.pub'):
                keys_found.append(str(key_file))

    return keys_found

def test_ssh_connection(host, username, key_path, port=22):
    """Test SSH connection with detailed error reporting."""
    print(f"\n[*] Testing connection to {username}@{host}:{port}")
    print(f"[*] Using key: {key_path}")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Check if key file exists
        if not os.path.exists(key_path):
            print(f"[ERROR] Key file not found: {key_path}")
            return False

        # Try to connect
        print("[*] Attempting connection...")
        client.connect(
            hostname=host,
            port=port,
            username=username,
            key_filename=key_path,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )

        print("[SUCCESS] SSH connection established!")

        # Test command execution
        print("[*] Testing command execution...")
        stdin, stdout, stderr = client.exec_command("pwd")
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            print(f"[SUCCESS] Command executed successfully. Working directory: {output}")
        if error:
            print(f"[WARNING] Command stderr: {error}")

        # Test another command
        print("[*] Testing system info...")
        stdin, stdout, stderr = client.exec_command("uname -a")
        output = stdout.read().decode().strip()
        if output:
            print(f"[INFO] System: {output}")

        client.close()
        print("[SUCCESS] Connection test completed successfully!")
        return True

    except paramiko.AuthenticationException as e:
        print(f"[ERROR] Authentication failed: {e}")
        print("[INFO] This means the SSH key is not authorized on the server")
        print("[INFO] Make sure you've added your public key to RunPod:")
        print("       1. Go to https://console.runpod.io/user/settings")
        print("       2. Add your SSH public key")
        return False

    except paramiko.SSHException as e:
        print(f"[ERROR] SSH error: {e}")
        return False

    except Exception as e:
        print(f"[ERROR] Connection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("RunPod SSH Connection Diagnostic Tool")
    print("=" * 70)

    # Find available keys
    print("\n[*] Searching for SSH keys...")
    keys = find_ssh_key()

    if keys:
        print(f"[INFO] Found {len(keys)} SSH key(s):")
        for key in keys:
            print(f"      - {key}")
    else:
        print("[ERROR] No SSH keys found!")
        print("[INFO] Generate a key with: ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_runpod")
        return

    # Read .env file for RunPod credentials
    print("\n[*] Reading RunPod credentials from .env file...")
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()

        ssh_lines = [line.strip() for line in lines if line.strip().startswith('ssh ')]

        if not ssh_lines:
            print("[ERROR] No SSH connection info found in .env file")
            return

        print(f"[INFO] Found {len(ssh_lines)} SSH connection(s) in .env file")

        # Parse SSH connections
        import re
        for idx, line in enumerate(ssh_lines, 1):
            print(f"\n[*] Testing connection #{idx}: {line}")

            # Parse username and host
            match = re.search(r"ssh\s+([^\s@]+)@([^\s]+)", line)
            if match:
                username = match.group(1)
                host = match.group(2)

                # Parse port
                port_match = re.search(r"\s-p\s+(\d+)", line)
                port = int(port_match.group(1)) if port_match else 22

                # Parse key path
                key_match = re.search(r"-i\s+([^\s]+)", line)
                if key_match:
                    key_path = os.path.expanduser(key_match.group(1))
                else:
                    # Default to id_ed25519_runpod
                    key_path = os.path.expanduser("~/.ssh/id_ed25519_runpod")

                test_ssh_connection(host, username, key_path, port)
            else:
                print(f"[WARNING] Could not parse SSH connection string: {line}")

    except FileNotFoundError:
        print("[ERROR] .env file not found")
    except Exception as e:
        print(f"[ERROR] Failed to read .env file: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Diagnostic completed")
    print("=" * 70)

if __name__ == "__main__":
    main()

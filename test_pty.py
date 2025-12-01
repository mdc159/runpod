"""
Test different PTY connection methods to RunPod
"""

import paramiko

def test_with_pty():
    """Test SSH connection with PTY requested."""
    print("Testing SSH with PTY request...")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            hostname='ssh.runpod.io',
            username='im5qj03lqzxugv-64410c77',
            key_filename='C:/Users/default.DESKTOP-A36S57H/.ssh/id_ed25519_runpod',
            look_for_keys=False,
            allow_agent=False
        )

        print("[SUCCESS] Connected!")

        # Test 1: Normal command (no PTY)
        print("\n[Test 1] Running command WITHOUT PTY...")
        stdin, stdout, stderr = client.exec_command("echo 'Hello from RunPod'")
        print(f"Output: {stdout.read().decode().strip()}")
        print(f"Stderr: {stderr.read().decode().strip()}")

        # Test 2: Request PTY
        print("\n[Test 2] Running command WITH PTY requested...")
        stdin, stdout, stderr = client.exec_command("echo 'Hello with PTY'", get_pty=True)
        print(f"Output: {stdout.read().decode().strip()}")
        print(f"Stderr: {stderr.read().decode().strip()}")

        # Test 3: Interactive command with PTY
        print("\n[Test 3] Running interactive shell command with PTY...")
        stdin, stdout, stderr = client.exec_command("bash -c 'pwd && whoami && hostname'", get_pty=True)
        print(f"Output: {stdout.read().decode().strip()}")

        # Test 4: Check if we can get an interactive shell
        print("\n[Test 4] Attempting to invoke interactive shell...")
        channel = client.invoke_shell()
        channel.send("pwd\n")
        import time
        time.sleep(1)
        output = channel.recv(1024).decode()
        print(f"Shell output: {output}")
        channel.close()

        client.close()
        print("\n[SUCCESS] All tests completed!")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_direct_ip():
    """Test direct IP connection (may support full PTY)."""
    print("\n" + "="*70)
    print("Testing Direct IP Connection (if pod is running)...")
    print("="*70)

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print("[*] Attempting connection to 149.36.1.233:40082...")
        client.connect(
            hostname='149.36.1.233',
            port=40082,
            username='root',
            key_filename='C:/Users/default.DESKTOP-A36S57H/.ssh/id_ed25519_runpod',
            timeout=5,
            look_for_keys=False,
            allow_agent=False
        )

        print("[SUCCESS] Direct IP connection established!")
        print("[INFO] This connection should support full PTY/interactive shell")

        # Test interactive shell
        print("\n[Test] Attempting interactive shell on direct connection...")
        channel = client.invoke_shell()
        channel.send("pwd\n")
        import time
        time.sleep(1)
        output = channel.recv(4096).decode()
        print(f"Shell output:\n{output}")
        channel.close()

        client.close()

    except Exception as e:
        print(f"[FAILED] {type(e).__name__}: {e}")
        print("[INFO] This likely means:")
        print("  - Your RunPod pod is stopped/paused")
        print("  - The pod was restarted with a new IP/port")
        print("  - Check https://console.runpod.io/ for current connection info")

if __name__ == "__main__":
    print("="*70)
    print("RunPod PTY Support Test")
    print("="*70)
    test_with_pty()
    test_direct_ip()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
For interactive shell access to RunPod:
1. Use RunPod Web Terminal: https://console.runpod.io/ (RECOMMENDED)
2. Get current direct SSH connection from RunPod console
3. Use ssh -L for port forwarding if needed

For programmatic access (scripts, automation):
- Current ssh.runpod.io connection works perfectly
- Use exec_command() without PTY for best results
""")

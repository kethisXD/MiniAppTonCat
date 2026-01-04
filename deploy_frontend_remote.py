import pty
import os
import time
import sys
import select

# Define parameters
password = "__SSH_PASSWORD__"
remote_host = "xxx@192.168.1.150"

commands = [
    "tar xzf frontend.tar.gz",
    "cd frontend",
    "docker build -t toncat-frontend .",
    "docker stop toncat-frontend || true",
    "docker rm toncat-frontend || true",
    "docker run -d --restart unless-stopped -p 3005:80 --name toncat-frontend toncat-frontend"
]

full_command = " && ".join(commands)
ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", remote_host, full_command]

print(f"Running remote deployment on {remote_host}...")
print(f"Command: {full_command}")

pid, fd = pty.fork()

if pid == 0:
    # Child
    os.execvp(ssh_cmd[0], ssh_cmd)
else:
    # Parent
    try:
        data = b""
        password_sent = False
        while True:
            r, _, _ = select.select([fd], [], [], 0.1)
            if not r:
                # Check if child exited
                if os.waitpid(pid, os.WNOHANG) != (0, 0):
                    break
                continue
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                data += chunk
                sys.stdout.buffer.write(chunk)
                sys.stdout.flush()
                
                if not password_sent and (b"password:" in chunk.lower() or b"password:" in data.lower()):
                    print("\nSending password...")
                    os.write(fd, password.encode() + b"\n")
                    password_sent = True
                    data = b"" # Reset buffer
            except OSError:
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        os.close(fd)
        # Ensure process is collected
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        print("\nDeployment execution finished.")

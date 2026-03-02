import pty
import os
import select
import time

def fix_hp_tailscale():
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        # 1. Write config pointing to Tailscale IP of RPi
        config = """api:
  listen: ":1984"

streams:
  cat_cam: rtsp://100.71.244.91:8554/feed
"""
        cmd_write = f"echo '{config}' > /home/xxx/go2rtc.yaml"
        # 2. Reload go2rtc via API
        cmd_reload = "curl -fsS -X POST http://127.0.0.1:1984/api/restart || echo 'Reload failed'"
        
        full_cmd = f"{cmd_write} && {cmd_reload}"
        
        # Connect to HP Server
        print(f"Connecting to HP Server to apply config: {config}")
        os.execlp("ssh", "ssh", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.150", full_cmd)
    else:
        # Parent
        output = b""
        password_sent = False
        
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r:
                break
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, b"__SSH_PASSWORD__\n")
                    password_sent = True
                    
            except OSError:
                break
                
        print(output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    fix_hp_tailscale()

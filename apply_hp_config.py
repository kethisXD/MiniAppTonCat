import pty
import os
import select
import time

def fix_hp():
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        # 1. Write config
        # 2. Reload go2rtc
        config = """api:
  listen: ":1984"

streams:
  cat_cam: http://127.0.0.1:5555/api/stream.flv?src=feed
"""
        cmd_write = f"echo '{config}' > /home/xxx/go2rtc.yaml"
        # Using built-in go2rtc API to reload config
        cmd_reload = "curl -X POST http://127.0.0.1:1984/api/config?src=config" # Or just reload? Usually restarting is safer if simplified reload fails, but let's try reload.
        # Actually, let's just kill it and assume the user's loop or manual start will pick it up? 
        # No, better to try API reload. 
        # If headers are needed...
        
        # Let's try simple file write then manual curl
        full_cmd = f"{cmd_write} && curl -fsS -X POST http://127.0.0.1:1984/api/restart || echo 'Reload failed'"
        
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
    fix_hp()

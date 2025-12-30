import pty
import os
import time
import select

def check_pi():
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        # Using StrictHostKeyChecking=no to avoid yes/no prompts
        os.execlp("ssh", "ssh", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.151", "hostname && ps aux | grep -E 'go2rtc|mediamtx|ffmpeg'")
    else:
        # Parent
        output = b""
        password_sent = False
        
        while True:
            r, _, _ = select.select([fd], [], [], 2.0)
            if not r:
                # Timeout
                break
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                
                # Simple heuristic for password prompt
                # Note: "xxx@192.168.1.151's password:"
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, b"__SSH_PASSWORD__\n")
                    password_sent = True
                    
            except OSError:
                break
                
        print("Output:", output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    check_pi()

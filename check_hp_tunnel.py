import pty
import os
import time
import select

def check_hp():
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        # Check if port 5555 is listening (Tunnel)
        # Using netstat or ss
        cmd = "ss -tulpn | grep 5555"
        os.execlp("ssh", "ssh", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.150", cmd)
    else:
        # Parent
        output = b""
        password_sent = False
        
        while True:
            r, _, _ = select.select([fd], [], [], 2.0)
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
                
        print("Output:", output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    check_hp()

import pty
import os
import select
import time

def diagnose_hp():
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        # Multi-step command to gather info
        cmd = "cat /home/xxx/go2rtc.yaml; echo '---PROCESS---'; ps aux | grep go2rtc; echo '---PORTS---'; ss -tulpn | grep 5555"
        os.execlp("ssh", "ssh", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.150", cmd)
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
    diagnose_hp()

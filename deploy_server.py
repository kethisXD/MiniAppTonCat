import pty
import os
import time
import select

def deploy():
    print("Deploying rpi_server.py to Raspberry Pi...")
    
    # scp -P 6969 ...
    cmd = "scp -P 6969 -o StrictHostKeyChecking=no /home/xxx/projects/MiniAppTonCat/test_servo_continuous.py xxx@192.168.1.151:~/tonCatNode/test_servo_continuous.py"
    
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        os.execv("/bin/sh", ["sh", "-c", cmd])
    else:
        # Parent
        output = b""
        password_sent = False
        
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r:
                # No data for 3 seconds, maybe done or waiting?
                # For SCP it might just be copying.
                # But we need to check if process is dead.
                try:
                    os.waitpid(pid, os.WNOHANG)
                except:
                    break
                # If still alive and no output, continue
                continue
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, b"__SSH_PASSWORD__\n")
                    password_sent = True
                    print("Password sent.")
                    
            except OSError:
                break
                
        print("Deployment finished.")
        print("Output:", output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    deploy()

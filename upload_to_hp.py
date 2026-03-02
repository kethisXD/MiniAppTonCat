import pty
import os
import select
import sys

def upload():
    password = b"__SSH_PASSWORD__\n"
    cmd = ["scp", "-o", "StrictHostKeyChecking=no", "rpi_server.py", "config.ini", "deploy_server.py", "xxx@192.168.1.150:~"]
    
    print(f"Running: {' '.join(cmd)}")
    pid, fd = pty.fork()
    
    if pid == 0:
        os.execvp(cmd[0], cmd)
    else:
        output = b""
        password_sent = False
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r:
                if os.waitpid(pid, os.WNOHANG) != (0, 0):
                    break
                continue
            
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                sys.stdout.write(chunk.decode(errors='ignore'))
                
                if not password_sent and b"password:" in output.lower():
                    os.write(fd, password)
                    password_sent = True
                    output = b""
            except OSError:
                break
        
        os.close(fd)
        os.waitpid(pid, 0)
        print("Upload complete.")

if __name__ == "__main__":
    upload()

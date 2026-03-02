import pty
import os
import select
import sys

def deploy_from_hp():
    password = b"__SSH_PASSWORD__\n"
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.150", 
           "SSH_PASSWORD='__SSH_PASSWORD__' python3 deploy_server.py"]
    
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
                sys.stdout.flush()
                
                if not password_sent and b"password:" in output.lower():
                    os.write(fd, password)
                    password_sent = True
                    output = b""
            except OSError:
                break
        
        os.close(fd)
        os.waitpid(pid, 0)
        print("\nDeploy from HP complete.")

if __name__ == "__main__":
    deploy_from_hp()

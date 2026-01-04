import pty
import os
import time
import select
import sys

def run_ssh(remote_cmd):
    print(f"Running remote command: {remote_cmd}")
    
    # ssh -p 6969 xxx@192.168.1.151 <command>
    cmd = ["ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.151", remote_cmd]
    
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        os.execvp("ssh", cmd)
    else:
        # Parent
        output = b""
        password_sent = False
        
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r:
                try:
                    os.waitpid(pid, os.WNOHANG)
                except:
                    break
                continue
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                
                # Check for password prompt
                # Note: prompts vary. "password:" is common.
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, b"__SSH_PASSWORD__\n")
                    password_sent = True
                    # print("Password sent.")
                    
            except OSError:
                break
                
        # print("Finished.")
        print(output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_remote.py '<command>'")
    else:
        run_ssh(sys.argv[1])

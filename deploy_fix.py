import pty
import os
import time
import select
import sys

def deploy_and_restart():
    # 1. SCP file
    print("Uploading rpi_server.py...")
    cmd_scp = ["scp", "-P", "6969", "-o", "StrictHostKeyChecking=no", "rpi_server.py", "xxx@192.168.1.151:~/tonCatNode/rpi_server.py"]
    run_interactive(cmd_scp)
    
    # 2. Restart server
    print("Restarting server...")
    # Kill old, start new with venv python
    # We use nohup and redirect output. 
    # Note: complex shell command needs to be passed as single string to ssh if feasible, or use sh -c
    remote_cmd = (
        "pkill -f rpi_server.py || true; "
        "sleep 2; "
        "cd ~/tonCatNode; "
        "nohup /home/xxx/testZero/.venv/bin/python rpi_server.py > server.log 2>&1 & "
        "sleep 2; "
        "cat server.log"
    )
    cmd_ssh = ["ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.151", remote_cmd]
    run_interactive(cmd_ssh)

def run_interactive(cmd_args):
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(cmd_args[0], cmd_args)
    else:
        output = b""
        password_sent = False
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r:
                try:
                    os.waitpid(pid, os.WNOHANG)
                except:
                    break
                continue # process still alive?
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, b"__SSH_PASSWORD__\n")
                    password_sent = True
                    # print("Password sent.")
            except OSError:
                break
        print(output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    deploy_and_restart()

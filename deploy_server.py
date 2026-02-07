import pty
import os
import time
import select

def deploy():
    print("Deploying rpi_server.py to Raspberry Pi...")
    
    # SCP
    cmd_scp = ["scp", "-P", "6969", "-o", "StrictHostKeyChecking=no", "rpi_server.py", "xxx@192.168.1.151:~/tonCatNode/rpi_server.py"]
    
    run_command(cmd_scp, "__SSH_PASSWORD__")
    
    # SSH Restart
    print("Restarting server process...")
    # Kill existing, then start new in background
    remote_cmd = "sudo pkill -f rpi_server.py; cd ~/tonCatNode && sudo nohup python3 rpi_server.py > server.log 2>&1 &"
    
    cmd_ssh = ["ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.151", remote_cmd]
    
    run_command(cmd_ssh, "__SSH_PASSWORD__")

def run_command(cmd, password):
    import pty
    import os
    import select
    import sys
    
    print(f"Running: {' '.join(cmd)}")
    pid, fd = pty.fork()
    
    if pid == 0:
        os.execvp(cmd[0], cmd)
    else:
        password_sent = False
        output = b""
        
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r:
                try:
                    if os.waitpid(pid, os.WNOHANG) != (0, 0):
                        break
                except:
                    break
                continue
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                sys.stdout.write(chunk.decode(errors='ignore')) # optional debug
                
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, password.encode() + b"\n")
                    password_sent = True
                    print("Password sent.")
                    
            except OSError:
                break
        
        os.close(fd)
        os.waitpid(pid, 0)
        print("Command finished.")


if __name__ == "__main__":
    deploy()

import pty
import os
import select
import time

def check_tailscale_logs():
    # Command to check logs and status
    remote_cmd = "sudo systemctl status tailscaled --no-pager -l && echo '--- LOGS ---' && sudo journalctl -u tailscaled -n 50 --no-pager"
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-t", "xxx@192.168.1.150", remote_cmd]
    
    print("Fetching Tailscaled logs from HP Server...")
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(cmd[0], cmd)
    else:
        output = b""
        password_sent = False
        
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
                # Simple password handler
                if not password_sent and (b"password:" in chunk.lower() or b"password:" in output[-50:].lower()):
                     os.write(fd, b"__SSH_PASSWORD__\n")
                     password_sent = True
            except OSError:
                break
        
        try:
             os.close(fd)
        except:
             pass
        os.waitpid(pid, os.WNOHANG)

        print(output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    check_tailscale_logs()

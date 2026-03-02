import pty
import os
import select
import time

def run_ssh_command(host, command, password="__SSH_PASSWORD__"):
    # Use array for execvp
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", f"xxx@{host}", command]
    if "100.71.244.91" in host:
        ssh_cmd = ["ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", f"xxx@{host}", command]

    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(ssh_cmd[0], ssh_cmd)
    else:
        output = b""
        password_sent = False
        start_time = time.time()
        
        while True:
            # 20s timeout for find command
            if time.time() - start_time > 20: 
                break

            r, _, _ = select.select([fd], [], [], 1.0)
            if not r:
                # Check exit
                if os.waitpid(pid, os.WNOHANG) != (0, 0):
                    break
                continue
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                
                out_str = output.decode("utf-8", errors="ignore")
                if not password_sent and ("password:" in out_str.lower()):
                    os.write(fd, (password + "\n").encode())
                    password_sent = True
            except OSError:
                break
                
        try: os.close(fd)
        except: pass
        try: os.waitpid(pid, os.WNOHANG)
        except: pass
             
        print(output.decode("utf-8", errors="ignore"))

def main():
    print("Searching for go2rtc on Pi...")
    # Search in home directory first, it's faster
    cmd = "find /home/xxx -name go2rtc -type f 2>/dev/null"
    run_ssh_command("100.71.244.91", cmd)

if __name__ == "__main__":
    main()

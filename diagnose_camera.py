import pty
import os
import select
import time
import sys

def run_ssh_command(host, command, password="__SSH_PASSWORD__"):
    print(f"--- Connecting to {host} ---")
    print(f"Command: {command}")
    
    # Use array for execvp
    if host == "100.71.244.91":
        ssh_args = ["ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", f"xxx@{host}", command]
    else:
        ssh_args = ["ssh", "-o", "StrictHostKeyChecking=no", f"xxx@{host}", command]

    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(ssh_args[0], ssh_args)
    else:
        output = b""
        password_sent = False
        start_time = time.time()
        
        while True:
            # 10s timeout per command
            if time.time() - start_time > 15:
                # Kill if stuck
                try:
                    os.kill(pid, 9)
                except:
                    pass
                output += b"\n[TIMEOUT]\n"
                break

            r, _, _ = select.select([fd], [], [], 1.0)
            if not r:
                # Check if child exited
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
                
        try:
            os.close(fd)
        except:
            pass
        # Ensure process cleanup
        try:
             os.waitpid(pid, os.WNOHANG)
        except:
             pass
             
        print(output.decode("utf-8", errors="ignore"))
        print("-" * 40)

def main():
    # 1. Check Pi - Robust check
    # Use ; to ensure all run even if one fails
    cmd_pi = "sudo systemctl status go2rtc --no-pager; echo '--- PORTS ---'; sudo netstat -tuln | grep 8554; echo '--- PS ---'; ps aux | grep go2rtc; echo '--- DOCKER ---'; docker ps"
    run_ssh_command("100.71.244.91", cmd_pi)

    # 2. Check HP Config
    cmd_hp = "cat /home/xxx/go2rtc.yaml; echo '--- PROJ CONFIG ---'; cat /home/xxx/projects/sshTonnelTonCatMiniApp/go2rtc.yaml"
    run_ssh_command("192.168.1.150", cmd_hp)

if __name__ == "__main__":
    main()

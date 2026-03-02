import pty
import os
import select
import time
import sys

def check_pi_config_correct():
    cmd = "cat /home/xxx/tonCatNode/config.ini"
    ssh_cmd = ["ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", "xxx@100.71.244.91", cmd]

    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(ssh_cmd[0], ssh_cmd)
    else:
        output = b""
        password_sent = False
        start_time = time.time()
        
        while True:
            if time.time() - start_time > 10:
                break
            r, _, _ = select.select([fd], [], [], 1.0)
            if not r:
                if os.waitpid(pid, os.WNOHANG) != (0, 0):
                    break
                continue
            
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                o_str = output.decode("utf-8", errors="ignore")
                
                if not password_sent and ("password:" in o_str.lower()):
                     os.write(fd, b"__SSH_PASSWORD__\n")
                     password_sent = True
            except OSError:
                break
                
        try: os.close(fd)
        except: pass
        try: os.waitpid(pid, os.WNOHANG)
        except: pass
        
        print(output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    check_pi_config_correct()

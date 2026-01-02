import pty
import os
import time
import select

def test_shell_gpio():
    print("Testing BCM 12 (Physical 32) via raspi-gpio...")
    
    # Commands to run on the Pi
    # 1. Set mode to output
    # 2. Turn ON
    # 3. Wait
    # 4. Turn OFF
    # 5. Reset to input (safety)
    
    cmds = [
        "raspi-gpio set 12 op",
        "echo 'Set Output. Turning ON...'",
        "raspi-gpio set 12 dh",
        "sleep 2",
        "echo 'Turning OFF...'",
        "raspi-gpio set 12 dl",
        "sleep 1",
        "echo 'Done.'"
    ]
    
    full_cmd = " && ".join(cmds)
    
    pid, fd = pty.fork()
    if pid == 0:
        os.execlp("ssh", "ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.151", full_cmd)
    else:
        output = b""
        password_sent = False
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r: break
            try:
                chunk = os.read(fd, 1024)
                if not chunk: break
                output += chunk
                
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, b"__SSH_PASSWORD__\n")
                    password_sent = True
            except OSError: break
            
        print("Output:", output.decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    test_shell_gpio()

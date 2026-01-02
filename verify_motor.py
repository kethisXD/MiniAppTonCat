import pty
import os
import time
import select

def verify_motor():
    pid, fd = pty.fork()
    if pid == 0:
        # Child
        # Check if the motor endpoint exists
        cmd = "curl -X POST http://127.0.0.1:8000/motor/on"
        os.execlp("ssh", "ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.151", cmd)
    else:
        # Parent
        output = b""
        password_sent = False
        
        while True:
            r, _, _ = select.select([fd], [], [], 3.0)
            if not r:
                break
                
            try:
                chunk = os.read(fd, 1024)
                if not chunk:
                    break
                output += chunk
                
                if not password_sent and (b"password:" in output.lower()):
                    os.write(fd, b"__SSH_PASSWORD__\n")
                    password_sent = True
                    
            except OSError:
                break
                
        result = output.decode("utf-8", errors="ignore")
        print("Output:", result)
        if '"status":"success"' in result:
            print("VERIFICATION PASSED: Motor endpoint is active.")
        else:
            print("VERIFICATION FAILED: Motor endpoint not found or error.")

if __name__ == "__main__":
    verify_motor()

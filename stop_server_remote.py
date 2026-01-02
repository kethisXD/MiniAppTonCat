import pty
import os
import time
import select

def restart_server():
    print("Attempting to restart backend server on Raspberry Pi...")
    
    # 1. Kill existing process
    kill_cmd = "pkill -f rpi_server.py"
    run_ssh_command(kill_cmd, "Stopping server...")
    
    time.sleep(2)
    
    # 2. Start new process
    # We use nohup to keep it running after SSH exits
    # And we redirect output to a log file so it doesn't hang the SSH session
    start_cmd = "nohup python3 /home/xxx/projects/MiniAppTonCat/rpi_server.py > /home/xxx/projects/MiniAppTonCat/server.log 2>&1 &"
    # Note: We need to make sure the path is correct on the PI.
    # The user lists file on LOCAL machine.
    # We don't know the exact path on the Pi! 
    # But usually it's mirrored or in a known place.
    # Let's check where the file is currently running from first.
    
    # Check running process to get path
    path_cmd = "ps -ef | grep rpi_server.py | grep -v grep"
    output = run_ssh_command(path_cmd, "Checking running path...")
    print(f"Process info: {output}")
    
    # Extract path (simple assumption)
    if "/home/" in output:
        # Try to parse path or just use the kill and manual start approach
        # Let's just Kill it first.
        pass
    else:
        print("Could not find running process. Maybe it is already stopped?")

    # If we simply KILL it, the user's terminal `fastApiPi` will return to prompt.
    # Then the user can restart it manually and SEE the logs.
    # This might be better than running it in background where logs are hidden.
    
    print("Server stopped. You should see the process end in your 'fastApiPi' terminal.")
    print("Please switch to that terminal and run: python3 rpi_server.py")

def run_ssh_command(cmd, description):
    print(description)
    pid, fd = pty.fork()
    if pid == 0:
        os.execlp("ssh", "ssh", "-p", "6969", "-o", "StrictHostKeyChecking=no", "xxx@192.168.1.151", cmd)
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
        return output.decode("utf-8", errors="ignore")

if __name__ == "__main__":
    restart_server()

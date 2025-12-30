from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import RPi.GPIO as GPIO
import uvicorn
import socket

# Try to import INA219
try:
    from ina219 import INA219, DeviceRangeError
    HAS_INA219 = True
except ImportError:
    HAS_INA219 = False

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# PIN CONFIG
LIGHT_PIN = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_PIN, GPIO.OUT)

# INA219 SETUP
ina = None
if HAS_INA219:
    try:
        ina = INA219(shunt_ohms=0.1)
        ina.configure()
    except:
        HAS_INA219 = False

def check_camera_status():
    """Check if go2rtc is listening on port 1984"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex(('127.0.0.1', 1984))
    sock.close()
    return result == 0

@app.get("/")
def read_root():
    return {"status": "Ready"}

@app.get("/status")
def get_status():
    # Voltage
    voltage = None
    if HAS_INA219 and ina:
        try: voltage = ina.voltage()
        except: pass
    
    # Camera Status
    cam_active = check_camera_status()

    return {
        "online": True, 
        "voltage": voltage,
        "camera_online": cam_active
    }

@app.post("/light/{state}")
def toggle_light(state: str):
    val = GPIO.HIGH if state.lower() == "on" else GPIO.LOW
    GPIO.output(LIGHT_PIN, val)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

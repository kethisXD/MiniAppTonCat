from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import RPi.GPIO as GPIO
import uvicorn
import socket
import time
import configparser
import os

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

# CONFIG LOAD
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)
IS_TESTNET = config.getboolean('DEFAULT', 'testnet', fallback=False)

# PIN CONFIG
LIGHT_PIN = 26
MOTOR_PIN = 18 # Physical Pin 12 (Servo)

# CONFIG VARIABLES
FEED_DURATION = config.getfloat('DEFAULT', 'feed_duration', fallback=0.5)
MOTOR_DURATION = config.getfloat('DEFAULT', 'motor_duration', fallback=0.5)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_PIN, GPIO.OUT)
GPIO.setup(MOTOR_PIN, GPIO.OUT)

# SERVO SETUP
# 50Hz frequency for servo
motor_pwm = GPIO.PWM(MOTOR_PIN, 50) 
motor_pwm.start(0) # Start with 0 duty (no signal)



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
    sensor_error = None
    
    if not HAS_INA219:
        sensor_error = "ina219 lib missing"
    elif ina is None:
        sensor_error = "ina219 init failed"
    else:
        try: 
            voltage = ina.voltage()
        except Exception as e: 
            sensor_error = f"Read Err: {str(e)}"
    
    # Camera Status
    cam_active = check_camera_status()

    return {
        "online": True, 
        "voltage": voltage,
        "sensor_error": sensor_error,
        "sensor_error": sensor_error,
        "camera_online": cam_active,
        "testnet": IS_TESTNET
    }

@app.post("/light/{state}")
def toggle_light(state: str):
    val = GPIO.HIGH if state.lower() == "on" else GPIO.LOW
    GPIO.output(LIGHT_PIN, val)
    return {"status": "success"}

@app.post("/motor/{state}")
def toggle_motor(state: str):
    print(f"Motor request: {state}")
    
    if state.lower() == "left":
        motor_pwm.ChangeDutyCycle(10)
        time.sleep(MOTOR_DURATION)
        motor_pwm.ChangeDutyCycle(0)
    elif state.lower() == "right":
        motor_pwm.ChangeDutyCycle(5)
        time.sleep(MOTOR_DURATION)
        motor_pwm.ChangeDutyCycle(0)
    else:
        motor_pwm.ChangeDutyCycle(0)
    
    return {"status": "success", "state": state}

@app.post("/feed")
def feed_cat():
    """
    Rotates the motor for FEED_DURATION seconds.
    Used for 'minimal donate' feature.
    """
    print(f"Feeding cat for {FEED_DURATION} seconds...")
    
    # Motor ON
    motor_pwm.ChangeDutyCycle(10)
    time.sleep(FEED_DURATION)
    
    # Motor OFF
    motor_pwm.ChangeDutyCycle(0)
    
    return {"status": "fed", "duration": FEED_DURATION}

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        motor_pwm.stop()
        GPIO.cleanup()

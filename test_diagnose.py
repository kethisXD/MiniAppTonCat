import RPi.GPIO as GPIO
import time

# Use BCM numbering to match the server code
GPIO.setmode(GPIO.BCM)

LIGHT_PIN = 26
MOTOR_PIN = 20 # Physical 38

GPIO.setup(LIGHT_PIN, GPIO.OUT)
GPIO.setup(MOTOR_PIN, GPIO.OUT)

print(f"Testing LIGHT (BCM {LIGHT_PIN}) and MOTOR (BCM {MOTOR_PIN})...")
print("Both should blink ON/OFF every 2 seconds.")
print("Press Ctrl+C to stop.")

try:
    while True:
        print("ON")
        GPIO.output(LIGHT_PIN, GPIO.HIGH)
        GPIO.output(MOTOR_PIN, GPIO.HIGH)
        time.sleep(2)
        print("OFF")
        GPIO.output(LIGHT_PIN, GPIO.LOW)
        GPIO.output(MOTOR_PIN, GPIO.LOW)
        time.sleep(2)
except KeyboardInterrupt:
    print("Stopping...")
    GPIO.cleanup()

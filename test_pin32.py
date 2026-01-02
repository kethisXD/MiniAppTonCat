import RPi.GPIO as GPIO
import time

# Use Physical Pin numbering
GPIO.setmode(GPIO.BOARD)

# Physical Pin 32
MOTOR_PIN = 32

GPIO.setup(MOTOR_PIN, GPIO.OUT)

print(f"Testing Physical Pin {MOTOR_PIN}...")
print("Press Ctrl+C to stop.")

try:
    while True:
        print("ON")
        GPIO.output(MOTOR_PIN, GPIO.HIGH)
        time.sleep(2)
        print("OFF")
        GPIO.output(MOTOR_PIN, GPIO.LOW)
        time.sleep(2)
except KeyboardInterrupt:
    print("Stopping...")
    GPIO.cleanup()

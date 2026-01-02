import RPi.GPIO as GPIO
import time

# PHYSICAL PIN 12 = BCM 18
MOTOR_PIN = 18 
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_PIN, GPIO.OUT)

# 50Hz PWM
p = GPIO.PWM(MOTOR_PIN, 50)
p.start(0)

print("--- SERVO CALIBRATION ---")
print("We will test different values. Tell me which one makes it SPIN SMOOTHLY.")

try:
    # 1. TEST NEUTRAL (STOP)
    print("Testing 7.5 (Neutral/Stop)...")
    p.ChangeDutyCycle(7.5)
    time.sleep(3)

    # 2. TEST SLOW FORWARD
    print("Testing 8.0 (Slow Forward)...")
    p.ChangeDutyCycle(8.0)
    time.sleep(3)
    
    # 3. TEST FAST FORWARD
    print("Testing 10.0 (Fast Forward)...")
    p.ChangeDutyCycle(10.0)
    time.sleep(3)

    # 4. TEST SLOW REVERSE
    print("Testing 7.0 (Slow Reverse)...")
    p.ChangeDutyCycle(7.0)
    time.sleep(3)

    # 5. TEST FAST REVERSE
    print("Testing 5.0 (Fast Reverse)...")
    p.ChangeDutyCycle(5.0)
    time.sleep(3)
    
    # 6. TEST STOP (0)
    print("Testing 0 (Signal Off)...")
    p.ChangeDutyCycle(0)
    time.sleep(3)

except KeyboardInterrupt:
    pass

p.stop()
GPIO.cleanup()
print("Done.")

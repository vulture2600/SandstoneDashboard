"""
Recover stuck i2c devices.
Stop all services using the i2c bus before running this script.
"""

import time
from RPi import GPIO

# BCM numbering
SCL_PIN = 3   # GPIO 3, physical pin 5
SDA_PIN = 2   # GPIO 2, physical pin 3

def i2c_bus_recover():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SCL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SDA_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    scl_high = GPIO.input(SCL_PIN)
    sda_high = GPIO.input(SDA_PIN)

    print(f"Before recovery: SCL={scl_high}, SDA={sda_high}")

    if scl_high and sda_high:
        print("Bus is free — no recovery needed.")
        GPIO.cleanup()
        return

    print("Attempting bus recovery...")

    # Temporarily take control of SCL
    GPIO.setup(SCL_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(SDA_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # keep SDA high

    # Toggle SCL up to 9 times
    for _ in range(9):
        if GPIO.input(SDA_PIN):  # SDA released, bus is free
            break
        GPIO.output(SCL_PIN, GPIO.LOW)
        time.sleep(0.001)
        GPIO.output(SCL_PIN, GPIO.HIGH)
        time.sleep(0.001)

    # Send a STOP if SDA is still low
    if not GPIO.input(SDA_PIN):
        print("Sending STOP condition...")
        GPIO.setup(SDA_PIN, GPIO.OUT, initial=GPIO.LOW)
        time.sleep(0.001)
        GPIO.output(SCL_PIN, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(SDA_PIN, GPIO.HIGH)

    GPIO.cleanup()
    print("Bus recovery complete.")

if __name__ == "__main__":
    i2c_bus_recover()

    print("Now run:")
    print("sudo rmmod i2c_bcm2835 && sudo modprobe i2c_bcm2835")

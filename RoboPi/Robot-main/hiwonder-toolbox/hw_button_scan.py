import os, sys, time
import RPi.GPIO as GPIO

key1_pin = 13
key2_pin = 23

def reset_wifi():
    os.system("rm /etc/Hiwonder/* -rf > /dev/null 2>&1")
    os.system("systemctl restart hw_wifi.service > /dev/null 2>&1")

servo_test = False
if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(key1_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(key2_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    key1_pressed = False
    key2_pressed = False
    count = 0
    while True:
        if GPIO.input(key1_pin) == GPIO.LOW:
            time.sleep(0.05)
            if GPIO.input(key1_pin) == GPIO.LOW:
                if key1_pressed == True:
                    count += 1
                    servo_test = True
                    if count == 60:
                        count = 0
                        servo_test = False
                        key1_pressed = False
                        print('reset_wifi')
                        reset_wifi()
            else:
                count = 0
                continue
            
        elif GPIO.input(key2_pin) == GPIO.LOW:
            time.sleep(0.05)
            if GPIO.input(key2_pin) == GPIO.LOW:
                if key2_pressed == True:
                    count += 1
                    if count == 60:
                        count = 0
                        key2_pressed = False
                        print('sudo halt')
                        os.system('sudo halt')
            else:
                count = 0
                continue
        else:
            if servo_test:
                servo_test = False
                os.system("sudo python3 /home/pi/TurboPi/HiwonderSDK/hardware_test.py")
                    
            count = 0
            if not key1_pressed:
                key1_pressed = True
            if not key2_pressed:
                key2_pressed = True
            time.sleep(0.05)

        

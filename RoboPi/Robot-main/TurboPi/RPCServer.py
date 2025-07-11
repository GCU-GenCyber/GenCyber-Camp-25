#!/usr/bin/python3
# coding=utf8
import os
import sys
sys.path.append('/home/pi/TurboPi/')
import time
import logging
import threading
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher
import HiwonderSDK as hwsdk
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import Functions.Running as Running
import Functions.lab_adjust as lab_adjust
import Functions.ColorDetect as ColorDetect_
import Functions.ColorTracking as ColorTracking_
import Functions.VisualPatrol as VisualPatrol_
import Functions.QuickMark as QuickMark_
import Functions.Avoidance as Avoidance_


if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

__RPC_E01 = "E01 - Invalid number of parameters!"
__RPC_E02 = "E02 - Invalid parameter!"
__RPC_E03 = "E03 - Operation failed!"
__RPC_E04 = "E04 - Operation timeout!"
__RPC_E05 = "E05 - Not callable"

HWSONAR = None
QUEUE = None

ColorDetect_.initMove()
ColorDetect_.setBuzzer(0.3)

car = mecanum.MecanumChassis()

@dispatcher.add_method
def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

data = []
@dispatcher.add_method
def SetPWMServo(*args, **kwargs):
    ret = (True, (), 'SetPWMServo')
    print("SetPWMServo:", args)
    arglen = len(args)
    try:
        servos = args[2:arglen:2]
        pulses = args[3:arglen:2]
        use_times = args[0]
        servos_num = args[1]
        data.insert(0, use_times)
        data.insert(1, servos_num)

        dat = zip(servos, pulses)
        for (s, p) in dat:
            pulses = int(map(p, 90, -90, 500, 2500))
            data.append(s)
            data.append(pulses)

        Board.setPWMServosPulse(data)
        data.clear()

    except Exception as e:
        print('error3:', e)
        ret = (False, __RPC_E03, 'SetPWMServo')
    return ret

@dispatcher.add_method
def SetMovementAngle(angle):
    print(angle)
    try:
        if angle == -1:
            car.set_velocity(0, 90, 0)
        else:
            car.set_velocity(70, angle, 0)
    except:
        ret = (False, __RPC_E03, 'SetMovementAngle')
        return ret

# Motor control
@dispatcher.add_method
def SetBrushMotor(*args, **kwargs):
    ret = (True, (), 'SetBrushMotor')
    arglen = len(args)
    print(args)
    if 0 != (arglen % 2):
        return (False, __RPC_E01, 'SetBrushMotor')
    try:
        motors = args[0:arglen:2]
        speeds = args[1:arglen:2]

        for m in motors:
            if m < 1 or m > 4:
                return (False, __RPC_E02, 'SetBrushMotor')

        dat = zip(motors, speeds)
        for m, s in dat:
            Board.setMotor(m, s)

    except:
        ret = (False, __RPC_E03, 'SetBrushMotor')
    return ret

# Get ultrasonic sensor distance measurement
@dispatcher.add_method
def GetSonarDistance():
    global HWSONAR
    ret = (True, 0, 'GetSonarDistance')
    try:
        ret = (True, HWSONAR.getDistance(), 'GetSonarDistance')
    except:
        ret = (False, __RPC_E03, 'GetSonarDistance')
    return ret

# Get current battery voltage
@dispatcher.add_method
def GetBatteryVoltage():
    ret = (True, 0, 'GetBatteryVoltage')
    try:
        ret = (True, Board.getBattery(), 'GetBatteryVoltage')
    except Exception as e:
        print(e)
        ret = (False, __RPC_E03, 'GetBatteryVoltage')
    return ret

# Set ultrasonic sensor RGB light mode
@dispatcher.add_method
def SetSonarRGBMode(mode=0):
    global HWSONAR
    HWSONAR.setRGBMode(mode)
    return (True, (mode,), 'SetSonarRGBMode')

# Set ultrasonic sensor RGB light color
@dispatcher.add_method
def SetSonarRGB(index, r, g, b):
    global HWSONAR
    print((r, g, b))
    if index == 0:
        HWSONAR.setPixelColor(0, Board.PixelColor(r, g, b))
        HWSONAR.setPixelColor(1, Board.PixelColor(r, g, b))
    else:
        HWSONAR.setPixelColor(index, (r, g, b))
    return (True, (r, g, b), 'SetSonarRGB')

# Set ultrasonic sensor flashing color and cycle
@dispatcher.add_method
def SetSonarRGBBreathCycle(index, color, cycle):
    global HWSONAR
    HWSONAR.setBreathCycle(index, color, cycle)
    return (True, (index, color, cycle), 'SetSonarRGBBreathCycle')

# Start ultrasonic sensor flashing
@dispatcher.add_method
def SetSonarRGBStartSymphony():
    global HWSONAR
    HWSONAR.startSymphony()
    return (True, (), 'SetSonarRGBStartSymphony')

# Set obstacle avoidance speed
@dispatcher.add_method
def SetAvoidanceSpeed(speed=50):
    print(speed)
    return runbymainth(Avoidance_.setSpeed, (speed,))

# Set ultrasonic sensor distance threshold
@dispatcher.add_method
def SetSonarDistanceThreshold(new_threshold=30):
    print(new_threshold)
    return runbymainth(Avoidance_.setThreshold, (new_threshold,))

# Get current obstacle avoidance distance threshold
@dispatcher.add_method
def GetSonarDistanceThreshold():
    return runbymainth(Avoidance_.getThreshold, ())

# Set color threshold
# Parameter: color LAB
# Example: [{'red': ((0, 0, 0), (255, 255, 255))}]
@dispatcher.add_method
def SetLABValue(*lab_value):
    return runbymainth(lab_adjust.setLABValue, lab_value)

# Retrieve color threshold values
@dispatcher.add_method
def GetLABValue():
    return (True, lab_adjust.getLABValue()[1], 'GetLABValue')

# Save color threshold values
@dispatcher.add_method
def SaveLABValue(color=''):
    return runbymainth(lab_adjust.saveLABValue, (color,))

@dispatcher.add_method
def HaveLABAdjust():
    return (True, True, 'HaveLABAdjust')

@Request.application
def application(request):
    dispatcher["echo"] = lambda s: s
    dispatcher["add"] = lambda a, b: a + b
    response = JSONRPCResponseManager.handle(request.data, dispatcher)

    return Response(response.json, mimetype='application/json')

def startRPCServer():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    run_simple('', 9030, application)

if __name__ == '__main__':
    startRPCServer()

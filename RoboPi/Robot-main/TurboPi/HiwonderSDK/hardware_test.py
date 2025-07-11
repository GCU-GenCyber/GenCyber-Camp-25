#!/usr/bin/python3
# coding=utf8
import sys
import time
sys.path.append('/home/pi/TurboPi/')
import HiwonderSDK.Board as Board

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)
    
print('''
**********************************************************
********************PWM舵机和电机测试************************
**********************************************************
----------------------------------------------------------
Official website:https://www.hiwonder.com
Online mall:https://hiwonder.tmall.com
----------------------------------------------------------
Tips:
 * 按下Ctrl+C可关闭此次程序运行，若失败请多次尝试！
----------------------------------------------------------
''')

Board.setPWMServoPulse(1, 1800, 300) 
time.sleep(0.3)
Board.setPWMServoPulse(1, 1500, 300) 
time.sleep(0.3)
Board.setPWMServoPulse(1, 1200, 300) 
time.sleep(0.3)
Board.setPWMServoPulse(1, 1500, 300) 
time.sleep(1.5)

Board.setPWMServoPulse(2, 1200, 300) 
time.sleep(0.3)
Board.setPWMServoPulse(2, 1500, 300) 
time.sleep(0.3)
Board.setPWMServoPulse(2, 1800, 300)
time.sleep(0.3)
Board.setPWMServoPulse(2, 1500, 300) 
time.sleep(1.5)

Board.setMotor(1, 45)
time.sleep(0.5)
Board.setMotor(1, 0)
time.sleep(1)
        
Board.setMotor(2, 45)
time.sleep(0.5)
Board.setMotor(2, 0)
time.sleep(1)

Board.setMotor(3, 45)
time.sleep(0.5)
Board.setMotor(3, 0)
time.sleep(1)

Board.setMotor(4, 45)
time.sleep(0.5)
Board.setMotor(4, 0)
time.sleep(1)

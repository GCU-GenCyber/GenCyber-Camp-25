import sys
sys.path.append('/home/pi/TurboPi/')
from HiwonderSDK.Board import *

def setServoPulse(id, pulse, use_time):
    setPWMServoPulse(id, pulse, use_time)
    

#!/usr/bin/python
import sys
import serial
import time
import os
import re
import logging
from logging.handlers import RotatingFileHandler

def main():
    device = "/dev/ttyUSB0"
    CurrentPowerInterval = 300 #in seconds (this value must be smaller than kWhInterval
    kWhInterval = 3600 # in seconds 

    CurrentPowerLogger = createLogger("currentpower", "/opt/ace3000/log/currentPower.log")
    kWhLogger = createLogger("kWh", "/opt/ace3000/log/kWh.log")
        
    while True:  
        #calculate time (in s) of next full hour
        timeNextHour = time.time() +  (kWhInterval - (time.time() % kWhInterval))
        s0(device, CurrentPowerLogger, CurrentPowerInterval, timeNextHour) #measurement every 10s
        d0(device, kWhLogger) # will be called every 3600s
    
    
    
    
    #s0(kWhLogger)
    #d0(CurrentPowerLogger)



# Creates the loggers for data logging - FHEM filelog format
def createLogger(name, path):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # add a rotating handler
    handler = RotatingFileHandler(path, maxBytes=1024*1024, backupCount=3)
    logger.addHandler(handler)

    # create a logging format
    formatter = logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d_%H:%M:%S")
    handler.setFormatter(formatter)
    
    return logger
 
def d0(device, Logger):
    # configure the serial connections (the parameters differs on the device you are connecting to)
    ser = serial.Serial(
                        port=device,
                        baudrate=300,
                        parity=serial.PARITY_EVEN, 
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.SEVENBITS,
                        timeout=3)

    ser.open()
    ser.flushInput()

    

    #request data
    ser.write("/?!\r\n")

    ace3000str = ""
    for i in range(0, 6):
        ace3000str += ser.readline()

    #print ace3000str

    match = re.search("1.8.0\(0*([1-9][0-9\.]+)", ace3000str)
    if match:
        meterReading = match.group(1)
        print meterReading
        Logger.info(meterReading)
      
    #request stop
    ser.write("/?!")

    ser.close()
    
    time.sleep(30)  #warten bis Stromzaehler wieder im S0 Modus ist  



# Calculates currently used power by use of S0 out of the powermeter
# parameters: 
#    Reference to logger
#    measurement every "waittime" seconds
#    repeat measurements till endtime
def s0(device, Logger, waittime, endtime):
    # configure the serial connections (the parameters differs on the device you are connecting to)
    #stty time 1 min 1 -icanon < /dev/ttyUSB0
    #stty -F /dev/ttyUSB0 0:4:cbd:0:3:1c:7f:15:4:1:1:0:11:13:1a:0:12:f:17:16:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0
    os.system("stty time 1 min 1 -icanon < " + device)
    ser = serial.Serial(port=device, timeout=None)
    ser.open()
    ser.flushInput()
    
    oldtime = 0
    newtime = 0
    index = 0

    while time.time() < endtime:
        ser.read()
        newtime = time.time()
        index = index + 1;
        
        #second measurement
        if oldtime != 0:
            deltatime = newtime - oldtime
            #1000 Pulse => 1kWh
            power = 3600 / deltatime
            print str(index) + "\t" +str(int(power))
            Logger.info(int(power))         
            
            oldtime = 0
            newtime = 0
            time.sleep(waittime) #reduce measurements
            ser.flushInput()
            
        else: #first measurement
            oldtime = newtime

    ser.close()
    


if __name__ == "__main__":
    main()






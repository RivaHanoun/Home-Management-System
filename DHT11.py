#!/usr/bin/env python3
#############################################################################
# Filename    : DHT11.py
# Description :	read the temperature and humidity data of DHT11
# Author      : freenove
# modification: 2020/10/16
########################################################################
import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT
DHTPin = 17     #define the pin of DHT11

def loop():
    dht = DHT.DHT(DHTPin)   #create a DHT class object
    counts = 0 # Measurement counts
    while(True):
        counts += 1
        print("Measurement counts: ", counts)
        for i in range(0,15):
            print(f"Attempt to read DHT11")
            chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                print("DHT11,OK!")
                break
            elif (chk is dht.DHTLIB_ERROR_CHECKSUM):
                print("DHT11, Checksum Error")
            elif (chk is dht.DHTLIB_ERROR_TIMEOUT):
                print("DHT11, Timeout Error")
            else:
                print("DHT11, Unknown Error")
            time.sleep(0.1)
        print("Humidity : %.2f, \t Temperature : %.2f \n"%(dht.humidity,dht.temperature))
        current_temp_f = round(dht.temperature * (9/5) + 32)
        print(f"{current_temp_f}")
        time.sleep(2)       
        
if __name__ == '__main__':
    print ('Program is starting ... ')
    try:
        loop()
    except KeyboardInterrupt:
        GPIO.cleanup()
        exit()  

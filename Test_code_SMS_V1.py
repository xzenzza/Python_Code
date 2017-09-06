#!/usr/bin/env python
from __future__ import division
from subprocess import PIPE, Popen
import psutil,time
import RPi.GPIO as GPIO
import smbus
import time,spidev
import urllib2
import simplejson as json  #  pip install simplejson
import ast
import sqlite3
import decimal
import os
import glob
import psutil
import socket
from threading import Thread
import re
import zipfile
import serial

def getserialCPU():
    try:
        #cpuserial= '0000000000000000'
        cpuserial= '0000000000000000'
        f=open('/proc/cpuinfo','r')
        for line in f:   
            if line[0:6]=='Serial':
               cpuserial=line[10:26]
        f.close()
    except Exception:
        cpuserial=0
        print 'err getserialCPU() ' 
        #end get cpu info
    return cpuserial
print "get serial cpu ",getserialCPU()
def getTemp():
    try:
        res=os.popen('vcgencmd measure_temp').readline()
        readTempCPU = (res.replace("temp=","").replace("'C\n",""))
        #print "TempCPU",TempCPU
        return readTempCPU
        #return(res.replace("temp=","").replace("'C\n",""))
    except Exception as e:
        readTempCPU = 0.0
        print e.message, e.args
        return readTempCPU
print "get temp cpu ",getTemp()
def check_ram():
    try:
        ram = psutil.phymem_usage()
        ram_total = ram.total / 2**20       # MiB.
        ram_used = ram.used / 2**20
        ram_free = ram.free / 2**20
        ram_percent_used = ram.percent
        #return ram_total ,ram_used ,ram_free ,ram_percent_used
        return ram_percent_used
    except Exception:
        return 0.00
print "get temp cpu ",check_ram()
ser = serial.Serial(
    #port='/dev/ttyS0',
    port='/dev/ttyUSB0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)



try:
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
    base_dir = '/sys/bus/w1/devices/'
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'

    def read_temp_raw():
        try:
            f = open(device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines
        except Exception:
            print '     Error read_temp_raw()'  
        

    def read_temp_ds18b20():
        try:
            lines = read_temp_raw()
            #--------------- while loop ds18b20-----------------
            #while lines[0].strip()[-3:] != 'YES':
            #    print"Err...............while loop ds18b20"
            #    time.sleep(0.2)
            #   lines = read_temp_raw()
            #   print read_temp_raw()
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
                temp_f = temp_c * 9.0 / 5.0 + 32.0
                return temp_c
                #return temp_c, temp_f
            
        except Exception:
            temp_c = 0.0
            return temp_c
            print '     Error read_temp_ds18b20()'   
except Exception:
    print '     Error DS18b20 Set Initial'

def adc_raed0(channel):
    try:
        spi = spidev.SpiDev()
        spi.open(0,0)   #--------- slave select (CE0)---------#
        time.sleep(0.001)
        r1 = spi.xfer2([4|2|(channel>>2),(channel&3)<<6,0])
        adc_out1 = ((r1[1]&15)<<8)+r1[2]
        spi.close()
    except Exception:
        adc_out1=0
        print '     err  adc_raed0()'        
    return adc_out1

def adc_raed1(channel):
    try:
        spi = spidev.SpiDev()
        spi.open(0,1)   #--------- slave select (CE1)---------#
        time.sleep(0.001)
        r2 = spi.xfer2([4|2|(channel>>2),(channel&3)<<6,0])
        adc_out2 = ((r2[1]&15)<<8)+r2[2]
        #print "Test---------------=%2.2f"%(adc_out2)
        spi.close()
    except Exception:
        adc_out2=0
        print '     err  adc_raed1() '        
    return adc_out2


#------------------------------------------------------------#
#---------------------- Set GPIO Initial --------------------#
#------------------------------------------------------------#
try:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    bus = smbus.SMBus(1)
    DEVICE = 0x20
    IODIRA = 0x00
    GPIOA  = 0x12
    OLATA  = 0x14
    IODIRB = 0x01
    GPIOB  = 0x13
    OLATB  = 0x15
    StatusBatt = 0x00
    percentBatt=0
 

    #-------------------------

    #--------------- PIN Reset MCP23017------------#
    GPIO.setup(36,GPIO.OUT)  
    GPIO.output(36,GPIO.HIGH) # active low
    #-----------Config MCP23017 ------------------ 
    bus.write_byte_data(DEVICE,IODIRA,0x00)
    bus.write_byte_data(DEVICE,OLATA,0x00)
    bus.write_byte_data(DEVICE,IODIRB,0x00)
    bus.write_byte_data(DEVICE,OLATB,0x00)


    GPIO.setup(11,GPIO.OUT) #-------red led pv
    GPIO.setup(13,GPIO.OUT) #-------green led pv
    #-------------------------------
    GPIO.setup(16,GPIO.OUT) #-------red led CG
    GPIO.setup(18,GPIO.OUT) #-------green led CG
    #-------------------------------
    GPIO.setup(29,GPIO.OUT) #-------red led inv
    GPIO.setup(31,GPIO.OUT) #-------green led inv
    #---------------------------------
    GPIO.setup(33,GPIO.OUT) #-------green led network
    #---------------------------------
    GPIO.setup(38,GPIO.OUT) #-------red led batt
    GPIO.setup(40,GPIO.OUT) #-------green led batt

    def check_Batt():
    
        GPIO.output(29,GPIO.HIGH) #-------red off led inv
        GPIO.output(31,GPIO.LOW) #-------green on led inv

        GPIO.output(11,GPIO.HIGH) #-------red off led pv
        GPIO.output(13,GPIO.LOW) #-------green on led pv
        #-------------------------------
        GPIO.output(16,GPIO.HIGH) #-------red off led CG
        GPIO.output(18,GPIO.LOW) #-------green on led CG
        #-------------------------------
        GPIO.output(29,GPIO.HIGH) #-------red off led inv
        GPIO.output(31,GPIO.LOW) #-------green on led inv
        #---------------------------------
        GPIO.output(33,GPIO.LOW) #-------green on led network
        #---------------------------------
        GPIO.output(38,GPIO.HIGH) #-------red off led batt
        GPIO.output(40,GPIO.LOW) #-------green on led batt
        time.sleep(1)

        GPIO.output(29,GPIO.LOW) #-------red off led inv
        GPIO.output(31,GPIO.HIGH) #-------green on led inv

        GPIO.output(11,GPIO.LOW) #-------red off led pv
        GPIO.output(13,GPIO.HIGH) #-------green on led pv
        #-------------------------------
        GPIO.output(16,GPIO.LOW) #-------red off led CG
        GPIO.output(18,GPIO.HIGH) #-------green on led CG
        #-------------------------------
        GPIO.output(29,GPIO.LOW) #-------red off led inv
        GPIO.output(31,GPIO.HIGH) #-------green on led inv
        #---------------------------------
        GPIO.output(33,GPIO.LOW) #-------green on led network
        #---------------------------------
        GPIO.output(38,GPIO.LOW) #-------red off led batt
        GPIO.output(40,GPIO.HIGH) #-------green on led batt
    
except Exception:
    print '     err  Set GPIO Initial '

def Level_Batt_LED():
    bus.write_byte_data(DEVICE,OLATB,0xC0)
    time.sleep(1)
    bus.write_byte_data(DEVICE,OLATB,0xFF)   #----off all green led level batt 
    bus.write_byte_data(DEVICE,OLATA,0x70|0x00)
    time.sleep(5)
    bus.write_byte_data(DEVICE,OLATA,0x70|0x01)
    
    """try:
        if percentBatt >= 100 :
            bus.write_byte_data(DEVICE,OLATB,0xC0)   #----on green led level batt....full,75,50,25,low,emtry (MSB|LSB)   
            StatusBatt = 0x70
            bus.write_byte_data(DEVICE,OLATA,StatusBatt|str_status_fan)   #----off red led level batt....25,low,emtry
            return StatusBatt

        elif (percentBatt >= 75)&(percentBatt < 100) :
            bus.write_byte_data(DEVICE,OLATB,0xE0)   #----on green led level batt....full,75,50,25,low,emtry (MSB|LSB)
            StatusBatt = 0x70 
            bus.write_byte_data(DEVICE,OLATA,StatusBatt|str_status_fan)   #----off red led level batt....25,low,emtry
            return StatusBatt

        elif (percentBatt >= 50)&(percentBatt < 75) :
            bus.write_byte_data(DEVICE,OLATB,0xF0)   #----on green led level batt....emtry,low,25,50            (MSB|LSB)
            StatusBatt = 0x70 
            bus.write_byte_data(DEVICE,OLATA,StatusBatt|str_status_fan)   #----off red led level batt....25,low,emtry
            return StatusBatt

        elif (percentBatt >= 25)&(percentBatt < 50) :
            bus.write_byte_data(DEVICE,OLATB,0xFF)   #----off all green led level batt              (MSB|LSB)
            StatusBatt = 0x80 
            bus.write_byte_data(DEVICE,OLATA,StatusBatt|str_status_fan)   #----on red led level batt....25,low,emtry
            return StatusBatt

        elif (percentBatt >= 10)&(percentBatt < 25) :
            bus.write_byte_data(DEVICE,OLATB,0xFF)   #----off all green led level batt              (MSB|LSB)
            StatusBatt = 0xC0
            bus.write_byte_data(DEVICE,OLATA,StatusBatt|str_status_fan)   #----on red led level batt....low,emtry
            return StatusBatt

        elif (percentBatt >= 0)&(percentBatt < 10) :
            bus.write_byte_data(DEVICE,OLATB,0xFF)   #----off all green led level batt              (MSB|LSB)
            StatusBatt = 0xE0 
            bus.write_byte_data(DEVICE,OLATA,StatusBatt|str_status_fan)   #----on red led level batt....emtry
            return StatusBatt

    except Exception:
        StatusBatt=0
        print '     err Level_Batt_LED '
        return StatusBatt
    """

def read_time():
    #print "read_time" + "Start"
    global real_date
    global real_time
    global uart_time

    """     uart_time = ""
    real_time = ""
    uart_time = ""  """
    uart_time = 0
    ser.flushInput()
    uart_time1 = ser.readline()
    print uart_time1
    time.sleep(1)
    try:
        
        if(uart_time1[0] == 'T'):
        #print "OK Time"
            uart_time = uart_time1[1:15]
        #print uart_time1[1:9]
            read_date = str(uart_time1[1:9])
        #real_date = str(read_date[0:4]+"/"+read_date[4:6]+"/"+read_date[6:9])
            real_date = str(read_date[0:4]+read_date[4:6]+read_date[6:9])
        #print "read_date",real_date
        #print uart_time1[9:15]
            read_time = str(uart_time1[9:15])
        #real_time = str(read_time[0:2]+"/"+read_time[2:4]+"/"+read_time[4:6])
            real_time = str(read_time[0:2]+read_time[2:4]+read_time[4:6])
    #"""    #print "read_time",real_time
    except Exception:
        uart_time = "T00000000000000"
    return uart_time


while True:
    
    print "adc 0 ",adc_raed0(0),adc_raed0(1),adc_raed0(2),adc_raed0(3),adc_raed0(4),adc_raed0(5),adc_raed0(6),adc_raed0(7)
    print "adc 1 ",adc_raed1(0),adc_raed1(1),adc_raed1(2),adc_raed1(3),adc_raed1(4),adc_raed1(5),adc_raed1(6),adc_raed1(7)
    #read_temp_ds18b20()
    Level_Batt_LED()
    read_time()
    check_Batt()

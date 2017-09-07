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

urlfirmware = "http://www.thaisolarmonitor.com/firmware/zone2/SolarLogFlow_06092016_zone2.zip"


def convert2dot(Val,dot):
    Xfront = int(0)
    Xback  = float(0.00)
    
    Xfront = int(Val - Xfront)
    Xback = float(Val - Xfront)
    if(dot == 1):
        Xback = int(Xback * 10)
        Xback = Xback / 10.00
        val = Xfront + Xback
    elif(dot == 2):
        Xback = int(Xback * 100)
        Xback = Xback / 100.00
        val = Xfront + Xback
    elif(dot == 3):
        Xback = int(Xback * 1000)
        Xback = Xback / 1000.000
        val = Xfront + Xback
    return val 

#------------------------------------------------------------#
#------------------------  getserialCPU  --------------------#
#------------------------------------------------------------#
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

#------------------------------------------------------------#
#------------------------   getTempCPU   --------------------#
#------------------------------------------------------------# 
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
    #time.sleep(5)

#------------------------------------------------------------#
#------------------------ check internet --------------------#
#------------------------------------------------------------# 
def check_internet():
    status=0
    try:    
        response=urllib2.urlopen('http://www.google.com',timeout=65)
        #print response.getcode()
        if(response.getcode()==200):
            status=response.getcode()
            check_connect=1
        else:
            status=0
            check_connect=0
    except Exception:
        status=0
        print '......check internet Errer web ouwaa soft ',Exception.message
    return str(status)  

#------------------------------------------------------------#
#---------------- create  function Check RAM ----------------#
#------------------------------------------------------------#
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

#------------------------------------------------------------#
#---------------- create  function Check IRR ----------------#
#------------------------------------------------------------# 
def check_irr(get_irr,load_wm):
    print("     irr = %2.2f wm2."%(get_irr))
    #print '     irr ==',get_irr
    chk =False
    try:
        if float(get_irr)>=float(load_wm):
            print '     * Normal irr >=200'
            chk =True
            if(float(get_irr) == 1000):
                IpvMAX = Ipv
                VpvMAX = Vpv 
                print("     IpvMAX = %2.2f A."%(IpvMAX))
                print("     VpvMAX = %2.2f V."%(VpvMAX))

        
        else:
            print '     * Fault irr <=200'
            chk =False
    except Exception:
        chk =False        
        print '     err  check_irr'
    return chk


#------------------------------------------------------------#
#---------------- create  function Check PV  ----------------#
#------------------------------------------------------------# 

def check_PV(VpvMax,IpvMax,Vpv,Ipv):
    checkPV = False
    #print '     Vpv = ', Vpv
    try:
        if((Vpv >= (0.1*VpvMax))&(Ipv >= (0.1*IpvMax))):
            GPIO.output(11,GPIO.HIGH) #-------red off led pv
            GPIO.output(13,GPIO.LOW) #-------green on led pv
            checkPV = True
            print '     * Normal PV'
        else:
            GPIO.output(11,GPIO.LOW) #-------red on led pv
            GPIO.output(13,GPIO.HIGH) #-------green off led pv

            if((Vpv >= (0.1*VpvMax))&(Ipv < (0.1*IpvMax))):
                print '         * Fault PV  Vpv = ',Vpv,' >= 0.1*VpvMax' '   Ipv = ',Ipv,' < 0.1*IpvMax'
            elif((Vpv < (0.1*VpvMax))&(Ipv >= (0.1*IpvMax))):
                print '         * Fault PV  Vpv = ',Vpv,' < 0.1*VpvMax' '    Ipv = ',Ipv,' >= 0.1*IpvMax'  

            elif((Vpv < (0.1*VpvMax))&(Ipv < (0.1*IpvMax))):
                print '         * Fault PV  Vpv = ',Vpv,' < 0.1*VpvMax' '    Ipv = ',Ipv,' < 0.1*IpvMax' 
            
            checkPV = False
    except Exception:
        checkPV = False
        print '     err check_PV()'

    return checkPV

#------------------------------------------------------------#
#----------- create  function Check Inverter  ---------------#
#------------------------------------------------------------# 
def check_Inverter(Vinv,Iinv):
    checkInv = False
    try:
        if((Vinv > 190)&(Vinv < 240)&(Iinv > 0)):
            #'         ---------- 190 < Vin :',Vin,' < 240  && Iinverter =',Iinv,'> 0  ------------'
            GPIO.output(38,GPIO.HIGH) #-------red off led batt
            GPIO.output(40,GPIO.LOW) #-------green off led batt

            #-------------------------------
            GPIO.output(29,GPIO.HIGH) #-------red off led inv
            GPIO.output(31,GPIO.LOW) #-------green on led inv

            checkInv = True
            print '     * Inverter working run Load , Unkonw Batt , Normal Inverter'
        else:
           # '         ---------- Vin ',Vin,' < 190  && Iinverter =',Iinv,'<= 0  ------------'
            checkInv = False
            print '     * Inverter working No Load'

        #time.sleep(1)
        

    except Exception:
        checkInv = False
        print '     err check_Inverter()'
    return checkInv

##------------------------------------------------##
##--------------------UART init-------------------##
##------------------------------------------------##

ser = serial.Serial(
    #port='/dev/ttyS0',
    port='/dev/ttyUSB0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

#------------------------------------------------------------#
#--------------------- Create Check BAtt --------------------#
#------------------------------------------------------------#
def check_Batt(PercentBATT):
    try:
        
        
        if(PercentBATT >= 50):
            Status =  1
            GPIO.output(38,GPIO.HIGH) #-------red off led batt
            GPIO.output(40,GPIO.LOW) #-------green on led batt
            print  Status
        else:
            Status =  0
            GPIO.output(38,GPIO.LOW) #-------red on led batt
            GPIO.output(40,GPIO.HIGH) #-------green off led batt
            print  Status
            
        return Status
    except Exception:
        Status = 3
        print '     err check_Batt()' 
        return Status

#------------------------------------------------------------#
#------------------ Create Check Charger --------------------#
#------------------------------------------------------------#
def check_charger(Icharger,Ipv,Vbatt,VbattMax,VbattMin,Iinverter,str_status_fan,percent_batt):

    try:
        if(Icharger > (0.1*Ipv)):
            GPIO.output(16,GPIO.HIGH) #-------red off led CG
            GPIO.output(18,GPIO.LOW) #-------green on led CG
            print '     * Normal Charger'

            if(Iinverter > 0):
                GPIO.output(29,GPIO.HIGH) #-------red off led inv
                GPIO.output(31,GPIO.LOW) #-------green on led inv
                print '     * Normal Inverter'

            else:
                if(Vbatt <= VbattMin):
                    GPIO.output(29,GPIO.HIGH) #-------red off led inv
                    GPIO.output(31,GPIO.HIGH) #-------green off led inv

                    str_status_batt = Level_Batt_LED(str_status_fan,percent_batt)
                    bus.write_byte_data(DEVICE,OLATA,(str_status_fan|str_status_batt))#Display LED Levelbatt & Control FAN
                    print '     * Unkown Inverter , Low Batt'
                else:
                    print '    * Fault alarm Inverter'
                    GPIO.output(29,GPIO.HIGH) #-------red off led inv
                    GPIO.output(31,GPIO.HIGH) #-------green off led inv
                    #time.sleep(0.5)

                    GPIO.output(29,GPIO.LOW) #-------red on led inv
                    GPIO.output(31,GPIO.HIGH) #-------green off led inv
                    #time.sleep(0.5)

                    GPIO.output(29,GPIO.HIGH) #-------red off led inv
                    GPIO.output(31,GPIO.HIGH) #-------green off led inv
                    #time.sleep(0.5)

                    GPIO.output(29,GPIO.LOW) #-------red on led inv
                    GPIO.output(31,GPIO.HIGH) #-------green off led inv
                    #time.sleep(0.5)

        else:
            if(Vbatt >= VbattMax):
                GPIO.output(16,GPIO.HIGH) #-------red off led CG
                GPIO.output(18,GPIO.HIGH) #-------green off led CG
                
                str_status_batt = Level_Batt_LED(str_status_fan,percent_batt)
                bus.write_byte_data(DEVICE,OLATA,(str_status_fan|str_status_batt))#Display LED Levelbatt & Control FAN
                print '     * Unknown Charger , Full Batt'
            else:
                print '     * Fault alarm Charger'
                GPIO.output(16,GPIO.HIGH) #-------red off led CG
                GPIO.output(18,GPIO.HIGH) #-------green off led CG
                #time.sleep(0.5)
                
                GPIO.output(16,GPIO.HIGH) #-------red off led CG
                GPIO.output(18,GPIO.LOW) #-------green on led CG
                #time.sleep(0.5)

                GPIO.output(16,GPIO.HIGH) #-------red off led CG
                GPIO.output(18,GPIO.HIGH) #-------green off led CG
                #time.sleep(0.5)
                
                GPIO.output(16,GPIO.HIGH) #-------red off led CG
                GPIO.output(18,GPIO.LOW) #-------green on led CG
                #time.sleep(0.5)
             

    except Exception:
        #checkCharger = False
        print '     err check_charger()'

    #return checkCharger
    
#------------------------------------------------------------#
#-------------------- DS18b20 Set Initial -------------------#
#------------------------------------------------------------#
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

#------------------------------------------------------------#
#---------------------- SPI 3208 Initial --------------------#
#------------------------------------------------------------#           
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

except Exception:
    print '     err  Set GPIO Initial '

#------------------------------------------------------------#
#----------------------  Level_Batt_LED  --------------------#
#------------------------------------------------------------#   
def Level_Batt_LED(str_status_fan,percentBatt):
    try:
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

#------------------------------------------------------------#
#-------------------------  Send_msg  -----------------------#
#------------------------------------------------------------#   
def Send_msg(xmsg):
    print 'message:',xmsg
    try:
        response_m=urllib2.urlopen('http://www.thaisolarmonitor.com/getmydata/savemessage.ashx?sn='+str(getserialCPU())+'&tm='+time.strftime('%Y%m%d%H%M%S')+'&msg='+xmsg.replace(" ","_")+'&prj=solar',timeout=15)
        #time.sleep (1)
        print response_m.getcode()
 
    except: # urllib2.request.URLError:
        print '......err  Connect Server..MESSAGE.....SEND....',time.strftime('%Y/%m/%d %H:%M:%S')
#----------------------- end  function send  msg   -----------------------------       


try:
    VRbatt1=0
    VRbatt2=0
    Cx = 0    
    msg="StartProgram"
    check_server_count =0

    led_pv=1
    led_charger=1
    led_inv=1
    led_batt=1
    led_power=1

    #Send_msg(" open Program")
    print '##################################'
    print 'serialcode:', getserialCPU()
    print '##################################'

    print 'check internet :',check_internet()
    urlx = "http://www.thaisolarmonitor.com/getmydata/getmydataconfigjson.ashx?sn="+str(getserialCPU())+"&fg=0"
    print 'load config urlx:',urlx
    #time.sleep(10)
except Exception:
    print '     err load config urlx'

try:
    #---------- LED Indicator Status  All  Clear   --------------- 
    GPIO.output(11,GPIO.HIGH) 
    GPIO.output(13,GPIO.HIGH)
        
    GPIO.output(38,GPIO.HIGH) 
    GPIO.output(40,GPIO.HIGH)

    GPIO.output(16,GPIO.HIGH)
    GPIO.output(18,GPIO.HIGH)

    GPIO.output(29,GPIO.HIGH)
    GPIO.output(31,GPIO.HIGH)

    GPIO.output(33,GPIO.HIGH)
        
    #---------- LED Indicator Status  All  Green   ---------------     
    GPIO.output(11,GPIO.HIGH) #-------red off led pv
    GPIO.output(13,GPIO.LOW) #-------green on led pv
    #---------------------------------         
    GPIO.output(38,GPIO.HIGH) #-------red off led batt
    GPIO.output(40,GPIO.LOW) #-------green on led batt
    #---------------------------------
    GPIO.output(16,GPIO.HIGH) #-------red off led CG
    GPIO.output(18,GPIO.LOW) #-------green on led CG
    #-------------------------------
    GPIO.output(29,GPIO.HIGH) #-------red off led inv
    GPIO.output(31,GPIO.LOW) #-------green on led inv
    #---------------------------------
    GPIO.output(33,GPIO.LOW) #-------green on led network
    
    

    """#---------- LED Indicator Status  All  Red   ---------------     
    GPIO.output(11,GPIO.LOW) #-------red on led pv
    GPIO.output(13,GPIO.HIGH) #-------green off led pv
    #---------------------------------         
    GPIO.output(38,GPIO.LOW) #-------red on led batt
    GPIO.output(40,GPIO.HIGH) #-------green off led batt
    #---------------------------------
    GPIO.output(16,GPIO.LOW) #-------red on led CG
    GPIO.output(18,GPIO.HIGH) #-------green off led CG
    #-------------------------------
    GPIO.output(29,GPIO.LOW) #-------red on led inv
    GPIO.output(31,GPIO.HIGH) #-------green off led inv
    #---------------------------------
    GPIO.output(33,GPIO.LOW) #-------green on led network
    """
except Exception:
    print '     Error Set GPIO LED Indicator '


try:
    SamplingDC = 1000
    SamplingAC = 1000
    SamplingTemp = 100
    SamplingLigth = 100
    SamplingUser = 100
    ConstanceVbatt = 12.00
    ConstanceVpv = 41.0
    #----------------CalCT DC------------------#
    offsetCTibatt = 2.507
    offsetCTicharger = 2.518
    
    MultiplyConstant = 100

    
except Exception:
    print '     Error Set Value GLOBAL'

try:
    bus.write_byte_data(DEVICE,OLATB,0xFF)   #----off all green led level batt              (MSB|LSB)
    bus.write_byte_data(DEVICE,OLATA,0xF0)   #----on red led level batt....emtry
except Exception:
    print '     Error off LED Level Batt'


def getData(name,delay):
    print name + " Start"
    

    #------ define value
    global Irr
    global TempPV
    global TempAMB
    global TempBox
    global Ipv
    global Vpv
    global Icharger

    global Vbatt
    global Ibatt1
    global Ibatt2

    global Vload
    global Iload
    global Vgen
    global Igen
    global Iinverter

    global rawIrr
    global rawTempPV
    global rawTempAMB
    global rawIpv
    global rawVpv
    global rawIcharger

    global rawVbatt
    global rawIbatt1
    global rawIbatt2

    global rawVload
    global rawIload
    global rawVgen
    global rawIgen
    global rawIinverter

    global led_pv
    global led_charger
    global led_inv
    global led_batt
    global led_power
    global led_internet

    try:
        print '     --------------------------------------------------------------------'
        print '     ---------------------     get data Function     --------------------'
        print '     --------------------------------------------------------------------'
        #----------------------------- PV -----------------------------------------------

            
            
        adc_Irr = 0.0
        adc_TempPV = 0.0
        adc_TempAMB = 0.0
        adc_Vpv = 0.0
        adc_Ipv = 0.0
        adc_Icharger = 0.0

        SumADC_Irr = 0.0
        SumADC_TempPV = 0.0
        SumADC_TempAMB = 0.0
        SumADC_Vpv = 0.0
        SumADC_Ipv = 0.0
        SumADC_Icharger = 0.0
                   
        rawIrr = 0.0
        rawTempPV = 0.0
        rawTempAMB = 0.0
        rawIpv = 0.0
        rawVpv = 0.0
        rawIcharger = 0.0

           
            #------------------------------------------------------------------------------------
            

            #---------------------------- Batt -------------------------------------------------       

        adc_Vbatt = 0.0
        adc_Ibatt1 = 0.0
        adc_Ibatt2 = 0.0

        SumADC_Vbatt = 0.0
        SumADC_Ibatt1 = 0.0
        SumADC_Ibatt2 = 0.0
     
        rawVbatt = 0.0
        rawIbatt1 = 0.0
        rawIbatt2 = 0.0
            #------------------------------------------------------------------------------------

            #---------------------------- Inverter -----------------------------------------------       

        adc_Vload = 0.0
        adc_Iload = 0.0
        adc_Vgen = 0.0
        adc_Igen = 0.0
        adc_Iinverter = 0.0
            
        SumADC_Vload = 0.0
        SumADC_Iload = 0.0
        SumADC_Vgen = 0.0
        SumADC_Igen = 0.0
        SumADC_Iinverter = 0.0

        rawVload = 0.0
        rawIload = 0.0
        rawVgen = 0.0
        rawIgen = 0.0
        rawIinverter = 0.0
            
        #------------------------------------------------------------------------------------
        Irr = 0.0
        TempPV = 0.0
        TempAMB = 0.0 
        TempBox = 0.0 
        Ipv = 0.0
        Vpv = 0.0
        Icharger = 0.0 

        Vbatt = 0.0 
        Ibatt1 = 0.0
        Ibatt2 = 0.0

        Vload = 0.0
        Iload = 0.0
        Vgen = 0.0
        Igen = 0.0
        Iinverter = 0.0

        led_pv = 1
        led_charger = 1
        led_inv = 1
        led_batt = 1
        led_power = 1
        led_internet = 1


        #------------------------------------------------------------------------------------
            
        Sampling = 500
        Offset = 2048
        
        for i in range(0,Sampling):
            try:
                adc_Irr = adc_raed0(0)                                  
                adc_TempPV = adc_raed0(1)                               
                adc_TempAMB = adc_raed0(2)                              
                adc_Vpv = adc_raed0(5)                                  
                adc_Ipv = adc_raed1(0)                                  
                adc_Icharger = adc_raed1(7)                             

                adc_Vbatt = adc_raed0(6)                               
                adc_Ibatt1 = adc_raed1(3)                               
                adc_Ibatt2 = adc_raed1(5)                               

                adc_Vload = adc_raed0(7)                               
                adc_Iload = adc_raed1(2)                               
                adc_Vgen = adc_raed1(6)                                
                adc_Igen = adc_raed1(4)                                
                adc_Iinverter = adc_raed1(1)                           

                if(adc_Vload >= Offset):
                    adc_Vload = (adc_Vload - Offset)
                elif(adc_Vload < Offset):
                    adc_Vload = (Offset - adc_Vload)

                if(adc_Iload >= Offset):
                    adc_Iload = (adc_Iload - Offset)
                elif(adc_Iload < Offset):
                    adc_Iload = (Offset - adc_Iload)

                if(adc_Vgen >= Offset):
                    adc_Vgen = (adc_Vgen - Offset)
                elif(adc_Vgen < Offset):
                    adc_Vgen = (Offset - adc_Vgen)

                if(adc_Igen >= Offset):
                    adc_Igen = (adc_Igen - Offset)
                elif(adc_Igen < Offset):
                    adc_Igen = (Offset - adc_Igen)

                                 
                SumADC_Irr = SumADC_Irr + adc_Irr
                SumADC_TempPV = SumADC_TempPV + adc_TempPV
                SumADC_TempAMB = SumADC_TempAMB + adc_TempAMB
                SumADC_Vpv = SumADC_Vpv + adc_Vpv
                SumADC_Ipv = SumADC_Ipv + adc_Ipv
                SumADC_Icharger = SumADC_Icharger + adc_Icharger

                SumADC_Vbatt = SumADC_Vbatt + adc_Vbatt
                SumADC_Ibatt1 = SumADC_Ibatt1 + adc_Ibatt1
                SumADC_Ibatt2 = SumADC_Ibatt2 + adc_Ibatt2

                SumADC_Vload = SumADC_Vload + adc_Vload
                SumADC_Iload = SumADC_Iload + adc_Iload
                SumADC_Vgen  = SumADC_Vgen + adc_Vgen
                SumADC_Igen  = SumADC_Igen + adc_Igen
                SumADC_Iinverter  = SumADC_Iinverter + adc_Iinverter

            except Exception:
                print '     Error for Sampling get data'


        SumADC_Irr = SumADC_Irr / Sampling
        SumADC_TempPV = SumADC_TempPV / Sampling
        SumADC_TempAMB = SumADC_TempAMB / Sampling
        SumADC_Vpv = SumADC_Vpv / Sampling
        SumADC_Ipv = SumADC_Ipv / Sampling
        SumADC_Ipv = float(format(SumADC_Ipv,'.0f'))
        SumADC_Icharger = SumADC_Icharger / Sampling
        SumADC_Icharger = float(format(SumADC_Icharger,'.0f'))
            
        SumADC_Vbatt = SumADC_Vbatt / Sampling
        SumADC_Ibatt1 = SumADC_Ibatt1 / Sampling
        SumADC_Ibatt1 = float(format(SumADC_Ibatt1,'.0f'))
        SumADC_Ibatt2 = SumADC_Ibatt2 / Sampling
        SumADC_Ibatt2 = float(format(SumADC_Ibatt2,'.0f'))

        SumADC_Vload = SumADC_Vload / Sampling
        SumADC_Vload = float(format(SumADC_Vload,'.0f'))
        SumADC_Iload = SumADC_Iload / Sampling
        SumADC_Iload = float(format(SumADC_Iload,'.0f'))
        SumADC_Vgen = SumADC_Vgen / Sampling
        SumADC_Vgen = float(format(SumADC_Vgen,'.0f'))
        SumADC_Igen = SumADC_Igen / Sampling
        SumADC_Igen = float(format(SumADC_Igen,'.0f'))
        SumADC_Iinverter = SumADC_Iinverter / Sampling
        SumADC_Iinverter = float(format(SumADC_Iinverter,'.0f'))
            

        print("     ADC Irr = %2.2f "%(SumADC_Irr))
        print("     ADC TempPV = %2.2f "%(SumADC_TempPV))
        print("     ADC TempAMB = %2.2f "%(SumADC_TempAMB))
        print("     ADC Vpv = %2.2f "%(SumADC_Vpv))
        print("     ADC Ipv = %2.2f "%(SumADC_Ipv))
        print("     ADC Icharger = %2.2f "%(SumADC_Icharger))

        print("     ADC Vbatt = %2.2f "%(SumADC_Vbatt))
        print("     ADC Ibatt1 = %2.2f "%(SumADC_Ibatt1))
        print("     ADC Ibatt2 = %2.2f "%(SumADC_Ibatt2))

        print("     ADC Vload = %2.2f "%(SumADC_Vload))
        print("     ADC Iload = %2.2f "%(SumADC_Iload))
        print("     ADC Vgen = %2.2f "%(SumADC_Vgen))
        print("     ADC Igen = %2.2f "%(SumADC_Igen))
        print("     ADC Iinverter = %2.2f "%(SumADC_Iinverter))


        rawIrr = (SumADC_Irr * 5.00)/4096                                
        rawIrr = float(format(rawIrr,'.3f'))
        rawTempPV = (SumADC_TempPV * 5.00)/4096                           
        rawTempPV = float(format(rawTempPV,'.3f'))
        rawTempAMB = (SumADC_TempAMB * 5.00)/4096                          
        rawTempAMB = float(format(rawTempAMB,'.3f'))
        rawVpv = (SumADC_Vpv * 5.00)/4096                               
        rawVpv = float(format(rawVpv,'.2f'))
        rawIpv = (SumADC_Ipv * 5.00)/4096                               
        rawIpv = convert2dot(rawIpv,3)
        rawIcharger = (SumADC_Icharger * 5.00)/4096                   
        rawIcharger = convert2dot(rawIcharger,3)


        rawVbatt = (SumADC_Vbatt * 5.00)/4096                           
        rawVbatt = float(format(rawVbatt,'.2f'))
        rawIbatt1 = (SumADC_Ibatt1 * 5.00)/4096                          
        rawIbatt1 = convert2dot(rawIbatt1,3)
        rawIbatt2 = (SumADC_Ibatt2 * 5.00)/4096                          
        rawIbatt2 = convert2dot(rawIbatt2,3)

        rawVload = (SumADC_Vload * 5.00)/4096                            
        rawVload = convert2dot(rawVload,3)
        rawIload = (SumADC_Iload * 5.00)/4096                           
        rawIload = convert2dot(rawIload,3)
        rawVgen = (SumADC_Vgen * 5.00)/4096                             
        rawVgen = convert2dot(rawVgen,3)
        rawIgen = (SumADC_Igen * 5.00)/4096                             
        rawIgen = convert2dot(rawIgen,3)
        rawIinverter = (SumADC_Iinverter * 5.00)/4096                              
        rawIinverter = convert2dot(rawIinverter,3)

        print("     rawIrr = %2.3f V."%(rawIrr))
        print("     rawTempPV = %2.3f V."%(rawTempPV))
        print("     rawTempAMB = %2.3f V."%(rawTempAMB))
        print("     rawVpv = %2.2f V."%(rawVpv))
        print'     rawIpv = ',rawIpv,'V.'
        print'     rawIcharger = ',rawIcharger,'V.'

        print("     rawVbatt = %2.2f V."%(rawVbatt))
        print'     rawIbatt1 = ',rawIbatt1,'V.'
        print'     rawIbatt2 = ',rawIbatt2,'V.'

        print'     rawVload = ',rawVload,'V.'
        print'     rawIload = ',rawIload,'V.'
        print'     rawVgen = ',rawVgen,'V.'
        print'     rawIgen = ',rawIgen,'V.'
        print'     rawIinverter = ',rawIinverter,'V.'

        Irr = rawIrr*(46600/1000)
        TempPV = (rawTempPV-0.69713)/(-0.00187)
        TempPV = TempPV + 3.74 #cal to STL
        TempPV = convert2dot(TempPV,2)

        TempAMB = (rawTempAMB-0.69713)/(-0.00187)
        TempAMB = TempAMB*1.06
        TempAMB = TempAMB +2.91  #Cal to STL
        TempAMB = convert2dot(TempAMB,2)

# ---------------------- Voltage --------------------------------
        Vpv = rawVpv * 45
        Vbatt = rawVbatt * 12         

        if(rawVgen >= 0.34) & (rawVgen < 0.39):
            Vgen = (rawVgen * 50) + 213
            Vgen = convert2dot(Vgen,2)
        elif(rawVgen < 0.34) & (rawVgen >= 0.04):
            Vgen = (rawVgen * 653.5211)
            Vgen = convert2dot(Vgen,2)
        elif(rawVgen < 0.04):
            Vgen = 0.0
                

        if(rawVload >= 0.34) & (rawVload < 0.39):
            Vload = (rawVload * 50) + 213
            Vload = convert2dot(Vload,2)
        if(rawVload < 0.34) & (rawVload >= 0.04):
            Vload = (rawVload * 653.5211)
            Vload = convert2dot(Vload,2)
        if(rawVload < 0.04):
            Vload = 0.0

# ---------------------- Idc --------------------------------

        if(rawIbatt1 >= 2.535):
            Ibatt1 = (rawIbatt1 - 2.532)/ 0.016
            if(Ibatt1 < 0):
                Ibatt1 = 0.0
        elif(rawIbatt1 < 2.535):
            Ibatt1 = 0.0
        Ibatt1 = convert2dot(Ibatt1,2)
        if(Ibatt1 > 0):
            Ibatt1 = (Ibatt1*0.9427)+0.2808
            Ibatt1 = convert2dot(Ibatt1,2)

        if(rawIbatt2 >= 2.522):
            Ibatt2 = (rawIbatt2 - 2.519)/ 0.016
            if(Ibatt2 < 0):
                Ibatt2 = 0.0
        elif(rawIbatt2 < 2.522):
            Ibatt2 = 0.0
        Ibatt2 = convert2dot(Ibatt2,2)
        if(Ibatt2 > 0):
            Ibatt2 = (Ibatt2*0.967)+0.2772
            Ibatt2 = convert2dot(Ibatt2,2)
            
        if(rawIpv >= 2.532):
            Ipv = (rawIpv - 2.529)/ 0.016
            if(Ipv < 0):
                Ipv = 0.0
        elif(rawIpv <  2.532):
            Ipv = 0.0
        Ipv = convert2dot(Ipv,2)
        if(Ipv > 0):
            Ipv = (Ipv*0.9577)+0.2442
            Ipv = convert2dot(Ipv,2) 

        if(rawIcharger >= 2.522):
            Icharger = (rawIcharger - 2.519)/ 0.016
            if(Icharger < 0):
                    Icharger = 0.0
        elif(rawIcharger <  2.522):
            Icharger = 0.0
        Icharger = convert2dot(Icharger,2)
        if(Icharger > 0):
            Icharger = (Icharger*0.9671)+0.284
            Icharger = convert2dot(Icharger,2)

        if(rawIinverter >= 2.510):
            Iinverter = (rawIinverter - 2.510)/ 0.010
            if(Iinverter < 0):
                Iinverter = 0.0
        elif(rawIinverter <  2.510):
            Iinverter = 0.0
        Iinverter = convert2dot(Iinverter,2)
        if(Iinverter > 0):
            Iinverter = (Iinverter*0.8737)+0.5768
            Iinverter = convert2dot(Iinverter,2)


# ---------------------- Iac --------------------------------
        if(rawIload <=  0.022):
            Iload = 0.0
            
        elif(rawIload > 0.022):
            Iload = (97.654 *rawIload) - 1.2718
            Iload = convert2dot(Iload,2)
            if(Iload < 0):
                Iload = 0.0

            
        if(rawIgen <=  0.022):
            rawIgen = 0.0

        elif(rawIgen > 0.022):
            Igen = (97.654 *rawIgen) - 1.2718
            Igen = convert2dot(Igen,2)
            if(Igen < 0):
                Igen = 0.0


                
            
        print'     Irr = ',Irr,'wm2.'
        print'     TempPV = ',TempPV,'C.'
        print'     TempAMB = ',TempAMB,'C.'
        TempBox = read_temp_ds18b20()
        try:
            # print '     TempBox =', TempBox ,'C'
            print("     TempBox = %2.2f C"%(TempBox))

        except Exception:
            TempBox = 0.0
            print '     Not equipped with 1-wire'

        print'     Vpv = ',Vpv,'V.'
        print'     Ipv = ',Ipv,'A.'
        print'     Vbatt = ',Vbatt,'V.'
        print'     Ibatt1 = ',Ibatt1,'A.'
        print'     Ibatt2 = ',Ibatt2,'A.'
        print'     Icharger = ',Icharger,'A.'
        print'     Iinverter = ',Iinverter,'A.'
        print'     Vload = ',Vload,'V.'
        print'     Iload = ',Iload,'A.'
        print'     Vgen = ',Vgen,'V.'
        print'     Igen = ',Igen,'A.'
            

            
                        #ser.write('Time')
            #ser.write('\r\n')
            #time.sleep(0.5)




    except Exception:
        print '\r'
        print '     ------------------------- Error get data Function ---------------------'

    time.sleep(delay)

def Check_Level_Batt(name,delay):
    print name + "Start"
    global percent_batt
    Vbatt = 50
    VbattMAX = 54.00 #-----------------if BATT 4 CELL VbattMAX = 54.00
    VbattMIN = 46.00
    #---------------Cal Culation Percent BATT 4 CELL-----------------#
    #Vbatt = 10
    percent_batt = ((Vbatt - VbattMIN)/(VbattMAX - VbattMIN))*100.00
    #print 'percent_batt =', percent_batt,'%'
    #percent_batt = (percent_batt*6.75)-575

    if(percent_batt >= 100):
        percent_batt = 100
    elif(percent_batt <= 0):
        percent_batt = 0
    print("     percent_batt = %2.2f percents"%(percent_batt))

    time.sleep(delay)

"""def CheckBatt():

    try:
             
        if(percent_batt >= 50):
            Status =  1
            GPIO.output(38,GPIO.HIGH) #-------red off led batt
            GPIO.output(40,GPIO.LOW) #-------green on led batt
            print  Status
        else:
            Status =  0
            GPIO.output(38,GPIO.LOW) #-------red on led batt
            GPIO.output(40,GPIO.HIGH) #-------green off led batt
            print  Status
            
        return Status
    except Exception:
        Status = 3
        print '     err check_Batt()' 
        return Status
"""


def read_time(name,delay):
    print name + "Start"
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
    time.sleep(delay)
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
        #print "read_time",real_time


def sendData(name,delay):
        
    try:

        print '     --------------------------------------------------------------------'
        print '     ---------------- start send data to server function ----------------'
        print '     --------------------------------------------------------------------'

        global flagedata 
            
        print '     ++++++++++++++++++++++++++++++++++++++++++++++++++'
        print '     led PV=', led_pv
        print '     led Charger=',led_charger
        print '     led INV=',led_inv
        print '     led Batt=',led_batt
        print '     led Power=',led_power

            

               
        #time.sleep(1)

        #cursor2.execute("INSERT INTO solarlog11 VALUES ("+str(uart_time)+","+str(real_date)+","+str(real_time)+","+str(flagedata)+","+str(Irr)+","+str(TempPV)+","+str(TempAMB) +","+str(TempBox)+","+str(Vpv)+","+str(Ipv)+","+str(Icharger)+","+str(Vbatt)+","+str(Ibatt1)+","+str(Ibatt2)+","+str(Vload)+","+str(Iload)+","+str(Vgen)+","+str(Igen)+","+str(Iinverter)+","+str(rawIrr)+","+str(rawTempPV)+","+str(rawTempAMB)+","+str(rawIpv)+","+str(rawVpv)+","+str(rawIcharger)+","+str(rawVbatt)+","+str(rawIbatt1)+","+str(rawIbatt2)+","+str(rawVload)+","+str(rawIload)+","+str(rawVgen)+","+str(rawIgen)+","+str(rawIinverter)+","+str(1)+","+str(1)+","+str(1)+","+str(check_ram())+");");
     

            
        str_send_url ='http://www.thaisolarmonitor.com/getmydata/savedataonline.ashx?sn='+str(getserialCPU())+'&date='+str(real_date)+'&time='+str(real_time)        +'&irr='+str(Irr)+'&temppv='+str(TempPV)+'&tempamb='+str(TempAMB)+'&tempbox='+str(TempBox)+'&vpv='+str(Vpv)+'&ipv='+str(Ipv)+'&icharger='+str(Icharger)     +'&vbatt='+str(Vbatt)+'&ibatt1='+str(Ibatt1)+'&ibatt2='+str(Ibatt2)+'&vload='+str(Vload)+'&iload='+str(Iload)+'&vgen='+str(Vgen)+'&igen='+str(Igen)+'&iinverter='+str(Iinverter)+'&raw_irr='+str(rawIrr)+'&raw_temppv='+str(rawTempPV)+'&raw_tempamb='+str(rawTempAMB)       +'&raw_ipv='+str(rawIpv)+'&raw_vpv='+str(rawVpv)+'&raw_icharger='+str(rawIcharger)+'&raw_vbatt='+str(rawVbatt)+'&raw_ibatt1='+str(rawIbatt1)+'&raw_ibatt2='+str(rawIbatt2)+'&raw_vload='+str(rawVload)+'&raw_Iload='+str(rawIload)+'&raw_Vgen='+str(rawVgen)       +'&raw_Igen='+str(rawIgen)+'&raw_Iinverter='+str(rawIinverter)+'&ledinv='+str(1)+'&statusbatt='+str(1)+'&percenbatt='+str(percent_batt)+'&tempcpu='+str(getTemp())+'&percentram='+str(check_ram())+'&led_inv='+str(led_inv)+'&led_pv='+str(led_pv)+'&led_charger='+str(led_charger)+'&led_batt='+str(led_batt)+'&led_internet='+str(led_internet)+'&time='+time.strftime('%Y%m%d%H%M%S')+'  '
        print '     str_send_url=',str_send_url

        #response=urllib2.urlopen('http://www.ouwaasoft.co.th',timeout=65)
        #+'&statusBatt='+str(check_BattCharg[0])+','+str(check_BattCharg[1])+','+str(check_BattCharg[2])+','+str(check_BattCharg[3])
        #response=urllib2.urlopen('http://www.thaisolarmonitor.com/getmydata/savedataonline.ashx?sn='+str(getserialCPU())+'&t1='+str(TempPV)+'&t1r='+str(rawTempPV)        +'&t2='+str(TempAMB)+'&t2r='+str(rawTempAMB)+'&t3='+str(TempBox)+'&t3r='+str(rawTemp3)+'&t4='+str(getTemp())+'&lx='+str(Irr)     +'&lxr='+str(rawLight)+'&vdc1='+str(Vpv)+'&Vpv_raw='+str(rawVpv)+'&vac='+str(Vinv)+'&Vinv_raw='+str(rawVinv)+'&ctdcpv='+str(Ipv)+'&Ipv_raw='+str(rawIpv)+'&ctac='+str(Iinv)+'&Iinv_raw='+str(rawIinv)+'&vdc2='+str(Vbatt)+'&Vbatt_raw='+str(rawVbatt)       +'&ctdc='+str(Ibatt)+'&Ibatt_raw='+str(rawIbatt)+'&vbatt1='+str(VRbatt1)+'&VRbatt1_raw='+str(VRbatt1)+'&vbatt2='+str(VRbatt2)+'&VRbatt2_raw='+str(VRbatt2)+'&Icharger='+str(Icharger)+'&Icharger_raw='+str(rawIcharger)       +'&ledpv='+str(led_pv)+'&ledcharger='+str(led_charger)+'&ledinv='+str(led_inv)+'&ledbatt='+str(led_batt)+'&ledpower='+str(led_power)+'&time='+time.strftime('%Y%m%d%H%M%S')+'  ',timeout=65)
        response=urllib2.urlopen(str_send_url ,timeout=65)
        #'&statusBatt='+str(check_BattCharg[0])+','+str(check_BattCharg[1])+','+str(check_BattCharg[2])+','+str(check_BattCharg[3])+
            
        print '     send Data Querystring '
        time.sleep (5)
        print 'response.getcode',response.getcode() ,'  Data sent OK....'
        flagedata = 0
        print "     **********************************************************"
        print "     ----connect---------->> send to server ---- --->>> DB---->>insert"
        print "     **********************************************************"


                
    except Exception: # urllib2.request.URLError:
                    #    print '......err  Connect Server...',time.strftime('%Y/%m/%d %H:%M:%S')
                    #    #print "err"+Exception.message
                    #Send_msg(" 2Canot connect Internet  err send json data")
        flagedata = 1
        print '     ---- err connect_server_ ---- '
      
    print   '       data save flagedata  online / offline ', flagedata

    time.sleep (delay)


def insertDataBase(name,delay):
    print name + " Start"
    try:
    #-----------------  INSERT DATA SQLite  -----------------------------

        #flagedata = 1
        print '     INSERT DATA SOLAR ',time.strftime('%Y/%d/%m %H:%M:%S')
        #print '     data save  online [0 online / 1  offline] ',flagedata

        time.sleep(1)
        #uart_time = time.strftime('%Y%d%m%H%M%S')
        #ser.write("     -->> INSERT INTO datasolar  VALUES ("+str(datetime)+","+str(TempPV)+","+str(TempAMB)+","+str(TempBox)+","'0.0'","+str(Irr)+","+str(Lux)+","+str(Vinv) +","+str(Vpv)+","+str(Vbatt)+","+str(Iinv)+","+str(Ipv)+","+str(Ibatt)+","+str(Icharger)+","'0.0'","'0.0'","+str(percent_batt)+","+str(datetime)+","+str(flagedata)+","+str(rawTempPV)+","+str(rawTempAMB)+","'0.0'","+str(rawLight)+","+str(rawVinv)+","+str(rawVpv)+","+str(rawVbatt)+","+str(rawIinv)+","+str(rawIpv)+","+str(rawIbatt)+","+str(rawIcharger)+","+str(VRbatt1)+","+str(VRbatt2)+"); ")
        #ser.write('\r\n')

        write_database = "INSERT INTO solarlog11 VALUES ("+str(time.strftime('%Y%m%d%H%M%S'))+","+str(real_date)+","+str(real_time)+","+str(flagedata)+","+str(Irr)+","+str(TempPV)+","+str(TempAMB) +","+str(TempBox)+","+str(Vpv)+","+str(Ipv)+","+str(Icharger)+","+str(Vbatt)+","+str(Ibatt1)+","+str(Ibatt2)+","+str(Vload)+","+str(Iload)+","+str(Vgen)+","+str(Igen)+","+str(Iinverter)+","+str(rawIrr)+","+str(rawTempPV)+","+str(rawTempAMB)+","+str(rawVpv)+","+str(rawIpv)+","+str(rawIcharger)+","+str(rawVbatt)+","+str(rawIbatt1)+","+str(rawIbatt2)+","+str(rawVload)+","+str(rawIload)+","+str(rawVgen)+","+str(rawIgen)+","+str(rawIinverter)+","+str(1)+","+str(percent_batt)+","+str(1)+","+str(check_ram())+","+str(led_inv)+","+str(led_pv)+","+str(led_charger)+","+str(led_batt)+","+str(led_internet)+");"
        #write_database = "INSERT INTO solarlog11 VALUES ("+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1) +","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+","+str(1)+");"

        #print "     -->> INSERT INTO solarlog11  VALUES ("+str(uart_time)+","+str(real_date)+","+str(real_time)+","+str(flagedata)+","+str(Irr)+","+str(TempPV)+","+str(TempAMB) +","+str(TempBox)+","+str(Vpv)+","+str(Ipv)+","+str(Icharger)+","+str(Vbatt)+","+str(Ibatt1)+","+str(Ibatt2)+","+str(Vload)+","+str(Iload)+","+str(Vgen)+","+str(Igen)+","+str(Iinverter)+","+str(rawIrr)+","+str(rawTempPV)+","+str(rawTempAMB)+","+str(rawIpv)+","+str(rawVpv)+","+str(rawIcharger)+","+str(rawVbatt)+","+str(rawIbatt1)+","+str(rawIbatt2)+","+str(rawVload)+","+str(rawIload)+","+str(rawVgen)+","+str(rawIgen)+","+str(rawIinverter)+","+str(1)+","+str(percent_batt)+","+str(1)+","+str(check_ram())+"); "
        print "-->>>",write_database
        dbconnect2 = sqlite3.connect("Solar11.db");            
        dbconnect2.row_factory = sqlite3.Row;
        cursor2 = dbconnect2.cursor();
        cursor2.execute(write_database);
            #cursor2.execute("INSERT INTO solarlog11 VALUES ("+str(uart_time)+","+str(real_date)+","+str(real_time)+","+str(flagedata)+","+str(Irr)+","+str(TempPV)+","+str(TempAMB) +","+str(TempBox)+","+str(Vpv)+","+str(Ipv)+","+str(Icharger)+","+str(Vbatt)+","+str(Ibatt1)+","+str(Ibatt2)+","+str(Vload)+","+str(Iload)+","+str(Vgen)+","+str(Igen)+","+str(Iinverter)+","+str(rawIrr)+","+str(rawTempPV)+","+str(rawTempAMB)+","+str(rawIpv)+","+str(rawVpv)+","+str(rawIcharger)+","+str(rawVbatt)+","+str(rawIbatt1)+","+str(rawIbatt2)+","+str(rawVload)+","+str(rawIload)+","+str(rawVgen)+","+str(rawIgen)+","+str(rawIinverter)+","+str(1)+","+str(percent_batt)+","+str(1)+","+str(check_ram())+","+str(led_inv)+","+str(led_pv)+","+str(led_charger)+","+str(led_batt)+","+str(led_internet)+");");
            ###cursor2.execute("INSERT INTO solarlog11 VALUES ("+str(uart_time)+","+str(real_date)+","+str(real_time)+","+str(flagedata)+","+str(Irr)+","+str(TempPV)+","+str(TempAMB) +","+str(TempBox)+","+str(Vpv)+","+str(Ipv)+","+str(Icharger)+","+str(Vbatt)+","+str(Ibatt1)+","+str(Ibatt2)+","+str(Vload)+","+str(Iload)+","+str(Vgen)+","+str(Igen)+","+str(Iinverter)+","+str(rawIrr)+","+str(rawTempPV)+","+str(rawTempAMB)+","+str(rawIpv)+","+str(rawVpv)+","+str(rawIcharger)+","+str(rawVbatt)+","+str(rawIbatt1)+","+str(rawIbatt2)+","+str(rawVload)+","+str(rawIload)+","+str(rawVgen)+","+str(rawIgen)+","+str(rawIinverter)+","+str(1)+","+str(percent_batt)+","+str(1)+","+str(check_ram())+");");
        dbconnect2.commit();
        print '     INSERT DATA Solar11 SQLite  OK. '

        dbconnect2.close();
    except Exception:
        print '     connect database -->sqllit insert  err'
            
    time.sleep(delay)




#t1 = Thread(target=getData, args=("getData Funtion :" ,10))
#t2 = Thread(target=Check_Level_Batt, args=("Check_Level_Batt :" ,15))
#t3 = Thread(target=read_time, args=("read_time :" ,1))
#t4 = Thread(target=sendData, args=("sendData :" ,20))
#t5 = Thread(target=insertDataBase, args=("insertDataBase Funtion :" ,25))

  

#t1.start()
#t2.start()
#t3.start()
#t4.start()
#t5.start()


while(1):
    getData("getData Funtion :" ,1)
    Check_Level_Batt("Check_Level_Batt :" ,1)
    read_time("read_time :" ,1)
    sendData("sendData :" ,1)
    insertDataBase("insertDataBase Funtion :" ,1)
    
    time.sleep(7)

   
    
    



    

    
        
            

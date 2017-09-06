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
    if(dot == 2):
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
        response=urllib2.urlopen('http://www.ouwaasoft.co.th',timeout=65)
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
"""def check_Batt(Ipv,Icharger,Ibatt,Iinverter,Vbatt):
    try:
        #Status = ""
        print "Ipv =",Ipv,"Icharger =",Icharger,"Ibatt =",Ibatt,"Iinverter =",Iinverter,"Vbatt =",Vbatt,
        if((Ipv > 0) &(Icharger > 0) &(Iinverter == 0)):
            Status =  "Charge",Vbatt,Ibatt,time.strftime('%Y%m%d%H%M%S')
            print  Status
        elif((Ipv > 0) &(Icharger > 0) &(Iinverter > 0)):
            Status =  "Charge&Load",Vbatt,Ibatt,time.strftime('%Y%m%d%H%M%S')
            print  Status
        elif((Ipv == 0) &(Icharger == 0) &(Iinverter == 0)):
            Status =  "DischargeNoLoad",Vbatt,Ibatt,time.strftime('%Y%m%d%H%M%S')
            print  Status
        elif((Ipv == 0) &(Icharger == 0) &(Iinverter > 0)):
            Status =  "DischargeLoad",Vbatt,Ibatt,time.strftime('%Y%m%d%H%M%S')
            print  Status
        return Status
    except Exception:
        Status = "err check_Batt()",Vbatt,Ibatt,time.strftime('%Y%m%d%H%M%S')
        print '     err check_Batt()' 
        return Status
"""

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
#------------------------- ReadIdc --------------------------#
#------------------------------------------------------------#  

def ReadIdc(ch):
    try:
        u = 0.0
        w = 0.0
        x = 0.0
        y = 0.0
        z = 0.0
        v = 0.0
        t = 0.0
        for i in range(0,1000):
            u = (adc_raed1(ch))*(4.993-0.006) / 4096
            w = (0.94500*w)+(0.0549000*u)
            x = (0.96900*x)+(0.0314590*w)
            y = (0.98750*y)+(0.0125660*x)
            #z = (0.99373*z)+(0.0062830*y)
            #v = (0.99683*v)+(0.0031415*z)
            #t = (0.99809*t)+(0.0018849*v) 
        return y
    except Exception:
        y = 0.0
        print '     err  ReadIdc '
        return y

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

"""try:
    print ' Load Config '
    response= urllib2.urlopen(urlx)
    print 'ok'
            
    if (str(check_internet())=='200'):            
        print ('get URL JSon --')
        data =response.read()
        print  'data json ',data

        data2=ast.literal_eval(data)
        print 'sn:', data2['sn']
        print 'irr:', data2['irr']
        print 'vpv1:', data2['vpv1']
        print 'ipv1:', data2['ipv1']
        print 'vpv2:', data2['vpv2']
        print 'ipv2:', data2['ipv2']
            
        print 'iinv1:', data2['iinv1']  #  inverter 
            
        print 'vbatt3:', data2['vbatt3']
            # ichange
        print 'ichange:', data2['ichange']
            # vbattcell1
        print 'vbattcell1:', data2['vbattcell1']
            # count1
        print 'count1:',data2['count1']
            # invout
        print 'invout:',data2['invout'] #  inverter out 
            # invcell2
        print 'vbattcell2:',data2['vbattcell2']
            # count2
        print 'count2:',data2['count2']
            # condatetime
            # delay1f1
        print 'delay1f1:',data2['delay1']
            # delay2f1
        print 'delay2f1:',data2['delay2']
            # delay3f2
        print 'delay3f2:',data2['delay3']
            # delay4f3
        print 'delay4f3:',data2['delay4']
            # delay5f3
        print 'delay5f3:',data2['delay5']
            # delay6f3
        print 'delay6f3:',data2['delay6']
            # delay7f3
        print 'delay7f3:',data2['delay7']
            
        print 'reboot:',data2['reboot']         

        print 'temp1cal:',data2['temp1cal']
        print 'temp2cal:',data2['temp2cal']
        print 'temp3cal:',data2['temp3cal']

        print 'vbattcal:',data2['vbattcal']
        print 'ibattcal:',data2['ibattcal']

        print 'ichargercal:',data2['ichargercal']

        print 'vrbatt1cal:',data2['vrbatt1cal']
        print 'vrbatt2cal:',data2['vrbatt2cal']

        print 'Luxcal:',data2['Luxcal']
            
        print 'vpvcal:',data2['vpvcal']
        print 'ipvcal:',data2['ipvcal']

        print 'vinvcal:',data2['vinvcal']
        print 'iinvcal:',data2['iinvcal']

        print 'vbattNcell1_full:',data2['vbattNcell1_full']
        print 'vbattNcell2_full:',data2['vbattNcell2_full']

        print 'vbattNcell1_empty:',data2['vbattNcell1_empty']
        print 'vbattNcell2_empty:',data2['vbattNcell2_empty']

        print 'ncell:',data2['ncell']
        print 'vinv1:',data2['vinv1']

        print 'updatefirmware:',data2['updatefirmware']
        print 'toserver:',data2['toserver']

        time.sleep(1)
        print ' DownLoad  Firmware   .  Update ......'
        if data2['updatefirmware'] ==1:
            try:
                file_name = urlfirmware .split('/')[-1]
                u = urllib2.urlopen(urlfirmware)
                f = open(file_name, 'wb')
                meta = u.info()
                file_size = int(meta.getheaders("Content-Length")[0])
                print "Ouwaa firmware Downloading : %s Bytes: %s" % (file_name, file_size)

                file_size_dl = 0
                block_sz = 8192
                while True:
                    buffer = u.read(block_sz)
                    if not buffer:
                        break

                    file_size_dl += len(buffer)
                    f.write(buffer)
                    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                    status = status + chr(8)*(len(status)+1)
                    print status,

                f.close()

                time.sleep(10)
                print ' .'
                #zf = zipfile.ZipFile('py_download_firmware.zip')

                def unzip(zip_file, outdir):
"""
                    #Unzip a given 'zip_file' into the output directory 'outdir'.
"""
                    zf = zipfile.ZipFile(zip_file, "r")
                    zf.extractall(outdir)
                    
                unzip("py_download_firmware.zip",".")
                print 'unzip ok .'

            except Exception:
                print 'frimware  ERRoR   download File ..'
                 
        else:
            print ' no update  firmware ....'

            
            # flagupdate
            #print 'flagupdate:',data2['flagupdate']
            
                       
        dbconnect = sqlite3.connect("SolarLog.db");            
        dbconnect.row_factory = sqlite3.Row;
            
        cursor = dbconnect.cursor();
        print '----------------------------------UPdate SQL3...0'
            #print "UPDATE config SET irr=%s,vpv1=%s,ipv1=%s,vpv2=%s,ipv2=%s   where idconfig=1; "%(data2['irr'],data2['vpv1'],data2['ipv1'],data2['vpv2'],data2['ipv2'])

            # ,data2['temp1cal'],data2['temp2cal'],data2['temp3cal'],data2['vbattcal'],data2['ibattcal'],data2['ichargercal'],data2['vrbatt1cal'],data2['vrbatt2cal'] ,data2['Luxcal'] ,data2['vpvcal'] ,data2['ipvcal'],data2['vinvcal']  ,data2['iinvcal'] ,data2['vbattNcell1_full']  ,data2['vbattNcell2_full']  ,data2['vbattNcell1_empty']  ,data2['vbattNcell2_empty'] ,data2['ncell'],data2['vinv1']
            #,temp1cal=?,temp2cal=?,temp3cal=?,vbattcal=?,ibattcal=?,ichargercal=?,vrbatt1cal=?,vrbatt2cal=? ,Luxcal=? ,vpvcal=?,ipvcal=?,vinvcal =? ,iinvcal=?  ,vbattNcell1_full =? ,vbattNcell2_full =? ,vbattNcell1_empty =? ,vbattNcell2_empty,ncell=?,vinv1=?
            
            #print '----------------------------------UPdate SQL3'            
        cursor.execute("UPDATE config SET irr=?,vpv1=?,ipv1=?,vpv2=?,ipv2=?,inv1=?,vbatt3=?,ichange=?,vbattcell1=?,count1=?,invout=?,invcell2=?,count2=?,delay1f1=?,delay2f1=?,delay3f2=?,delay4f3=?,delay5f3=?,delay6f3=?,delay7f3=?,temp1cal=?,temp2cal=?,temp3cal=?,vbattcal=?,ibattcal=?,ichargercal=?,vrbatt1cal=?,vrbatt2cal=? ,Luxcal=? ,vpvcal=?,ipvcal=?,vinvcal =? ,iinvcal=?  ,vbattNcell1full =? ,vbattNcell2full =? ,vbattNcell1empty =? ,vbattNcell2empty=?,ncell=?,vinv1=?     where idconfig=1;",(data2['irr'],data2['vpv1'],data2['ipv1'],data2['vpv2'],data2['ipv2'],data2['iinv1'],data2['vbatt3'],data2['ichange'],data2['vbattcell1'],data2['count1'],data2['invout'],data2['vbattcell2'],data2['count2'],data2['delay1'],data2['delay2'],data2['delay3'],data2['delay4'],data2['delay5'],data2['delay6'],data2['delay7'],data2['temp1cal'],data2['temp2cal'],data2['temp3cal'],data2['vbattcal'],data2['ibattcal'],data2['ichargercal'],data2['vrbatt1cal'],data2['vrbatt2cal'] ,data2['Luxcal'] ,data2['vpvcal'] ,data2['ipvcal'],data2['vinvcal']  ,data2['iinvcal'] ,data2['vbattNcell1_full']  ,data2['vbattNcell2_full']  ,data2['vbattNcell1_empty']  ,data2['vbattNcell2_empty'] ,data2['ncell'],data2['vinv1']   ));
            
        dbconnect.commit();            
        print ' commit() UPDATE DATABASE SQLite Config  OK. '
        print ' **** UPDATE Config DATABASE SQLite  OK.  ****'
            ##dbconnect.close();
            #cursor.execute('SELECT * FROM config');
            ##print data
            #for row in cursor:
            #    print(row['idconfig'],row['irr'],row['vpv1'])
            #    #close the connection
        dbconnect.close();
        print '++Close Sqlite3++'
    else:
            #check_internet=0
        print 'not load url  config '
        msg="not load url config"
except Exception: 
        print 'ERROR not URL load   configupdate to SQLite '
"""

        



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

while(1):

    print '**********************************************************'
    print '**********************  Start Loop  **********************'
    print '**********************************************************'

    #------------------------------------------------------------#
    #-------------------- Claer IDC function --------------------#
    #------------------------------------------------------------#

    u = 0.0
    w = 0.0
    x = 0.0
    y = 0.0
    z = 0.0
    v = 0.0
    t = 0.0


    
    #------------------------------------------------------------#
    #-----------------------Battery function---------------------#
    #------------------------------------------------------------#
    try:
        print '     --------------------------------------------------------------------'
        print '     ---------------------Working on Battery Function--------------------'
        print '     --------------------------------------------------------------------'

        adc_Vbatt = 0.0
        adc_Ibatt = 0.0
        SumADC_Vbatt = 0.0
        SumADC_Ibatt = 0.0
        rawIbatt = 0.0 
        rawVbatt = 0.0
        Ibatt = 0.0
        Vbatt = 0.0
    
        VbattMAX = 54.00 #-----------------if BATT 4 CELL VbattMAX = 54.00
        VbattMIN = 46.00
        #VbattMAX = 27.00 #-----------------if BATT 2 CELL VbattMAX = 27.00
        #VbattMIN = 23.00
        #VbattMAX = 12.73 #-----------------if BATT 2 CELL VbattMAX = 12.73
        #VbattMIN = 10.8
        #MultiplyIbatt = 0.9218 #CT2DC
        #MinusIbatt = 0.2333 #CT2DC             ##***----------Old CT
        MultiplyIbatt = 50#CT2DC
        MinusIbatt = 127.1 #CT2DC
        percent_batt = 0.0
        for i in range(0,SamplingDC):
            try:
                
                adc_Vbatt = adc_raed0(6) # read ADC Vbatt
                adc_Ibatt = adc_raed1(2)# rawIbatt
                SumADC_Vbatt = SumADC_Vbatt + adc_Vbatt
                SumADC_Ibatt = SumADC_Ibatt + adc_Ibatt
            except Exception:
                print '     Error for SamplingDC Batt'

       
        SumADC_Vbatt = SumADC_Vbatt / SamplingDC
        SumADC_Ibatt = SumADC_Ibatt / SamplingDC
        SumADC_Ibatt = float(format(SumADC_Ibatt,'.0f'))
        print("     ADC Vbatt = %2.2f "%(SumADC_Vbatt))
        print("     ADC Ibatt = %2.2f "%(SumADC_Ibatt))

       
        rawIbatt = ((SumADC_Ibatt*5.00)/4096) # rawIbatt
        rawIbatt = convert2dot(rawIbatt,3)    # 3 dot
        rawIbatt = rawIbatt - 0.02
#        rawIbatt = float(format(rawIbatt,'.3f'))
        rawVbatt = ((SumADC_Vbatt*5.00)/4096) # rawVbatt
        rawVbatt = float(format((rawVbatt),'.2f'))
        print'     rawIbatt = ',rawIbatt,'V.'
#        print("     rawIbatt = %2.3f V."%(rawIbatt))
        print("     rawVbatt = %2.2f V."%(rawVbatt))
        
        if(rawIbatt >= 0.08):
            
            Ibatt = ((rawIbatt*15.654)-1.4445)
            Ibatt = Ibatt - 0.4
            Ibatt = convert2dot(Ibatt,2)
            #Ibatt = float(format(Ibatt,'.2f'))
            #Ibatt = (rawIbatt - 2.5676)/0.016
            #Ibatt = (rawIbatt - 2.5)/0.016
            #Ibatt = (rawIbatt * MultiplyIbatt) - MinusIbatt
            if(Ibatt < 0):
                Ibatt = 0.0
                
        elif(rawIbatt <  0.08):
            Ibatt = 0.0
        Vbatt = (rawVbatt*ConstanceVbatt)
        Vbatt = float(format(Vbatt,'.2f'))
        
        #Vbatt = Vbatt * 4 #********************************************************
        print'     Ibatt = ',Ibatt,'A.'
        #print("     Ibatt = %2.2f A."%(Ibatt))
        print("     Vbatt = %2.2f V."%(Vbatt))
        #time.sleep(1)

        
        """if Vbatt>=54:
           percent_batt=100
        elif Vbatt<54 and Vbatt>=52:
           percent_batt=75
        elif Vbatt<52  and Vbatt>=50:
           percent_batt=50
        elif Vbatt<50  and Vbatt >=48:
           percent_batt=25
        elif Vbatt<48  and Vbatt >=46:
           percent_batt=24
        else:
           percent_batt=0

        #Level_Batt_LED(percent_batt)
#        str_status_batt = Level_Batt_LED(str_status_fan,percent_batt)

        print '     Percent =', percent_batt,'%'
        #print '     Status batt =', str_status_batt
        #Level_Batt_LED(100)
        """




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
        #print '     percent_batt = ', percent_batt,' %'

        #percent_batt = 100
        #Level_Batt_LED(percent_batt) #---------------------DisplayLevelBatt
        #Level_Batt_LED(0) #---------------------DisplayLevelBatt
        
        #time.sleep(1)
        print "      Percent Ram Used.. = ",check_ram()
        
    except Exception:
        print '\r'
        print '     ------------------------- Error Battery function ---------------------'
 
        #time.sleep(1)


    try:
        print '     --------------------------------------------------------------------'
        print '     -----------------------   Control Fan Function  --------------------'
        print '     --------------------------------------------------------------------'

    #------------------------------------------------------------#
    #------------------ Control Fan Function --------------------#
    #------------------------------------------------------------#
        
        #read_temp = 30
        TempSET = 30.00
        #percent_batt = 100
        if(float(read_temp_ds18b20()) >= TempSET):      #if(float(read_temp_ds18b20()) >= TempSET):
            str_status_fan = 0x01
            str_status_batt = Level_Batt_LED(str_status_fan,percent_batt)
            bus.write_byte_data(DEVICE,OLATA,(str_status_fan|str_status_batt))#Display LED Levelbatt & Control FAN
            print '         ---------- Temp Box = ', float(read_temp_ds18b20()) ,' >= ',TempSET,' C ---------'
            print '                     ------------- Fan ON ------------'

                
            #elif(read_temp_ds18b20() < 45.00):
        elif(float (read_temp_ds18b20()) < TempSET):
            str_status_fan = 0x00
            str_status_batt = Level_Batt_LED(str_status_fan,percent_batt)
            bus.write_byte_data(DEVICE,OLATA,(str_status_fan|str_status_batt))#Display LED Levelbatt & Control FAN
            print '         ---------- Temp Box = ', float(read_temp_ds18b20()) ,' < ',TempSET,' C ---------'
            print '                     ------------- Fan OFF ------------'

        #time.sleep(1) 
    except Exception:
        print '\r'
        print '     ----------------------- Error Control Fan Function  ------------------'

        #time.sleep(1)    
    #------------------------------------------------------------#
    #-----------------------  Temp function ---------------------#
    #------------------------------------------------------------#
    try:
        print '     --------------------------------------------------------------------'
        print '     ---------------------   Working on Temp Function  ------------------'
        print '     --------------------------------------------------------------------'

        SumADC_Temp1 = 0.0
        SumADC_Temp2 = 0.0
        SumADC_Temp3 = 0.0
        rawTemp1 = 0.0
        rawTemp2 = 0.0
        rawTemp3 = 0.0
        Temp1 = 0.0
        Temp2 = 0.0
        Temp3 = 0.0
        rawTempBox = 0.0
        TempBox = read_temp_ds18b20()
        
        for i in range(0,SamplingTemp):
            try:
                adc_Temp1 = adc_raed0(1)# # read ADC TempPV
                adc_Temp2 = adc_raed0(2)# # read ADC TempAMB
                adc_Temp3 = adc_raed0(3)# # read ADC Temp3

                SumADC_Temp1 = SumADC_Temp1 + adc_Temp1
                SumADC_Temp2 = SumADC_Temp2 + adc_Temp2
                SumADC_Temp3 = SumADC_Temp3 + adc_Temp3

            except Exception:
                print '     Error for SamplingTemp'

        SumADC_Temp1 = (SumADC_Temp1 / SamplingTemp)  
        SumADC_Temp2 = (SumADC_Temp2 / SamplingTemp)
        SumADC_Temp3 = (SumADC_Temp3 / SamplingTemp) 

        print("     ADC Temp1 = %2.2f "%(SumADC_Temp1))
        print("     ADC Temp2 = %2.2f "%(SumADC_Temp2))
        #print("     ADC Temp3 = %2.2f "%(SumADC_Temp3)) 
        
        rawTempPV = (SumADC_Temp1*(5.00 - 0.006))/4096 # rawTemp1
        rawTempAMB = (SumADC_Temp2*(5.00 - 0.006))/4096 # rawTemp2
        rawTemp3 = (SumADC_Temp3*(5.00 - 0.006))/4096 # rawTemp3
        
        print("     rawTempPV = %2.4f V."%(rawTempPV))
        print("     rawTempAMB = %2.4f V."%(rawTempAMB))
       # print("     rawTempBox = %2.4f V."%(rawTempBox))

        
        TempPV = (rawTempPV-0.69713)/(-0.00187)
        TempPV = TempPV + 3.74 #cal to STL
        TempAMB = (rawTempAMB-0.69713)/(-0.00187)
        TempAMB = TempAMB*1.06
        TempAMB = TempAMB +2.91  #Cal to STL
        Temp3 = (rawTemp3-0.69713)/(-0.00187)
        
        
        print '     TempCPU =', getTemp() ,'C'
        #print("     TempCPU = %2.2f C"%(getTemp()))

        try:
           # print '     TempBox =', TempBox ,'C'
            print("     TempBox = %2.2f C"%(TempBox))

        except Exception:
            TempBox = 0.0
            print '     Not equipped with 1-wire'

        print("     TempPV = %2.2f C"%(TempPV))
        print("     TempAMB = %2.2f C"%(TempAMB))
        #time.sleep(5)
        
    except Exception:
        TempBox = 0.0
        print("     TempBox = %2.2f C"%(TempBox))

        print '\r'
        print '     ------------------------- Error Temp function ----------------------'

        #time.sleep(1)


    #------------------------------------------------------------#
    #-----------------------  Light function ---------------------#
    #------------------------------------------------------------#
    try:
        print '     --------------------------------------------------------------------'
        print '     ---------------------   Working on Light function  -----------------'
        print '     --------------------------------------------------------------------'

        SumADC_Light = 0.0
        rawLight = 0.0
        Lux = 0.0
        Irr = 0.0

        for i in range(0,SamplingLigth):
            try:
                adc_LS = adc_raed0(0)# # read ADC Ligth

                SumADC_Light = SumADC_Light + adc_LS
            
            except Exception:
                print '     Error for SamplingLigth'


        SumADC_Light = (SumADC_Light / SamplingLigth)
        print("     ADC Light = %2.2f "%(SumADC_Light))

        rawLight = (SumADC_Light*5.2797)/4096 # rawLight
        rawLight = float(format(rawLight,'.2f'))
        print("     rawLight = %2.2f V."%(rawLight))
        
        Lux = (rawLight*rawLight*3467.2)+(5479.5*rawLight) #SL046
        
        Irr = (rawLight * 295.4) *0.92 #----0.92 factor STL
        Irr = float(format(Irr,'.2f'))
        print("     Lux = %2.2f Lux"%(Lux))
        print("     Irr = %2.2f wm2."%(Irr))

        #time.sleep(1)
    except Exception:
        print '\r'
        print '     ------------------------- Error Light function ----------------------'

        #time.sleep(1)


    #------------------------------------------------------------#
    #-----------------------   PV function  ---------------------#
    #------------------------------------------------------------#
    try:
        print '     --------------------------------------------------------------------'
        print '     ---------------------   Working on PV Function  --------------------'
        print '     --------------------------------------------------------------------'

        adc_Vpv = 0.0
        adc_Ipv = 0.0
        SumADC_Vpv = 0.0
        SumADC_Ipv = 0.0
        rawIpv = 0.0
        rawVpv = 0.0
        Ipv = 0.0
        Vpv = 0.0
        IpvP3 = 0.0
        MultiplyIpv = 62.258 #CT1DC
        MinusIpv = 158.26    #CT1DC
        
        for i in range(0,SamplingDC):
            try:
                adc_Vpv = adc_raed0(5)   # read ADC Vpv
                adc_Ipv = adc_raed1(0)   # read ADC Ipv
                SumADC_Vpv = SumADC_Vpv + adc_Vpv
                SumADC_Ipv = SumADC_Ipv + adc_Ipv
            except Exception:
                print '     Error for SamplingDC PV'


        SumADC_Vpv = SumADC_Vpv / SamplingDC
        SumADC_Ipv = SumADC_Ipv / SamplingDC
        SumADC_Ipv = float(format(SumADC_Ipv,'.0f'))
        print("     ADC Vpv = %2.2f "%(SumADC_Vpv))
        print("     ADC Ipv = %2.2f "%(SumADC_Ipv))

        rawIpv = (SumADC_Ipv*5.00)/4096 # rawIpv
#        rawIpv = float(format(rawIpv,'.3f'))
        rawIpv = convert2dot(rawIpv,3)
        rawVpv = (SumADC_Vpv*5.00)/4096 # rawVpv
        rawVpv = float(format(rawVpv,'.2f'))
        print'     rawIpv = ',rawIpv,'V.'
        #print("     rawIpv = %2.3f V."%(rawIpv))
        print("     rawVpv = %2.2f V."%(rawVpv))

        if(rawIpv >= 0.08):
            Ipv = ((rawIpv*15.654)-1.4445)
            Ipv = Ipv +0.3
            Ipv = convert2dot(Ipv,2)
            #Ipv = float(format(Ipv,'.3'))
            
            #Ipv = (rawIpv - 2.5638)/0.016
            if(Ipv<0):
                Ipv = 0.0
            #Ipv = (Ipv * MultiplyIpv) - MinusIpv
        elif(rawIpv <  0.08):
            Ipv = 0.0

        Vpv = rawVpv * ConstanceVpv
        Vpv = float(format(Vpv,'.2f'))
        print'     Ipv = ',Ipv,'A.'
        #print("     Ipv = %2.2f A."%(Ipv))
        print("     Vpv = %2.2f V."%(Vpv))

        #time.sleep(1)
    except Exception:
        print '\r'
        print '     ------------------------- Error PV function ---------------------'

        #time.sleep(1)

    #------------------------------------------------------------#
    #-----------------------   INV function  --------------------#
    #------------------------------------------------------------#
    try:
        print '     --------------------------------------------------------------------'
        print '     ------------------   Working on Inverter Function  -----------------'
        print '     --------------------------------------------------------------------'


        SumADC_Iinv = 0.0
        SumADC_Vinv = 0.0
        rawIinv = 0.0
        rawVinv = 0.0
        Iinv = 0.0
        Vinv = 0.0
        ConstanceVinv1 = 0.0333
        Offset = 2540

        SumADC_Iinv1 = 0.0
        SumADC_Vinv1 = 0.0
        rawIinv1 = 0.0
        rawVinv1 = 0.0
        Iinv1 = 0.0
        Vinv1 = 0.0

        SumADC_Iinv2 = 0.0
        SumADC_Vinv2 = 0.0
        rawIinv2 = 0.0
        rawVinv2 = 0.0
        Iinv2 = 0.0
        Vinv2 = 0.0


        for i in range(0,SamplingAC):
            try:
                adc_Iinv = adc_raed1(3)# # read ADC Iinv ADC 1.3
                adc_Iinv1 = adc_raed1(3)# # read ADC Iinv ADC 1.3
                adc_Iinv2 = adc_raed1(3)# # read ADC Iinv ADC 1.3
                adc_Vinv = adc_raed0(7)# read ADC Vinv
                adc_Vinv1 = adc_raed0(7)# read ADC Vinv
                adc_Vinv2 = adc_raed0(7)# read ADC Vinv
                time.sleep(0.001)
                #------------------------------------------------#
                #----------------- I Inverter -------------------#
                #------------------------------------------------#
                if(adc_Iinv >= Offset):
                    adc_Iinv = (adc_Iinv - Offset)
                elif(adc_Iinv < Offset):
                    adc_Iinv = (Offset - adc_Iinv)
                if(adc_Iinv1 >= Offset):
                    adc_Iinv1 = (adc_Iinv1 - Offset)
                elif(adc_Iinv1 < Offset):
                    adc_Iinv1 = (Offset - adc_Iinv1)
                if(adc_Iinv2 >= Offset):
                    adc_Iinv2 = (adc_Iinv2 - Offset)
                elif(adc_Iinv2 < Offset):
                    adc_Iinv2 = (Offset - adc_Iinv2)
                #------------------------------------------------#
                #----------------- V Inverter -------------------#
                #------------------------------------------------#
                if(adc_Vinv >= 2040):
                    adc_Vinv = (adc_Vinv - 2040)
                elif(adc_Vinv < 2040):
                    adc_Vinv = (2040 - adc_Vinv)
                if(adc_Vinv1 >= 2040):
                    adc_Vinv1 = (adc_Vinv1 - 2040)
                elif(adc_Vinv1 < 2040):
                    adc_Vinv1 = (2040 - adc_Vinv1)
                if(adc_Vinv2 >= 2040):
                    adc_Vinv2 = (adc_Vinv2 - 2040)
                elif(adc_Vinv2 < 2040):
                    adc_Vinv2 = (2040 - adc_Vinv2)

                SumADC_Iinv = SumADC_Iinv + adc_Iinv
                SumADC_Iinv1 = SumADC_Iinv1 + adc_Iinv1
                SumADC_Iinv2 = SumADC_Iinv2 + adc_Iinv2
                SumADC_Vinv = SumADC_Vinv + adc_Vinv
                SumADC_Vinv1 = SumADC_Vinv1 + adc_Vinv1
                SumADC_Vinv2 = SumADC_Vinv2 + adc_Vinv2
            except Exception:
                print '     Error for SamplingAC Inverter'

       

        SumADC_Iinv = SumADC_Iinv / SamplingAC
        SumADC_Iinv = float(format(SumADC_Iinv,'.0f'))
        SumADC_Iinv1 = SumADC_Iinv1 / SamplingAC
        SumADC_Iinv1 = float(format(SumADC_Iinv1,'.0f'))
        SumADC_Iinv2 = SumADC_Iinv2 / SamplingAC
        SumADC_Iinv2 = float(format(SumADC_Iinv2,'.0f'))
        SumADC_Iinv = (SumADC_Iinv + SumADC_Iinv1 + SumADC_Iinv2)/3.0000
        SumADC_Iinv = float(format(SumADC_Iinv,'.0f'))




        SumADC_Vinv = SumADC_Vinv / SamplingAC
        SumADC_Vinv = float(format(SumADC_Vinv,'.0f'))
        SumADC_Vinv1 = SumADC_Vinv1 / SamplingAC
        SumADC_Vinv1 = float(format(SumADC_Vinv1,'.0f'))
        SumADC_Vinv2 = SumADC_Vinv2 / SamplingAC
        SumADC_Vinv2 = float(format(SumADC_Vinv2,'.0f'))
        SumADC_Vinv = (SumADC_Vinv + SumADC_Vinv1 + SumADC_Vinv2)/3.00
        SumADC_Vinv = float(format(SumADC_Vinv,'.0f'))
        print("     ADC Iinverter = %2.0f "%(SumADC_Iinv))
        print("     ADC Vinverter = %2.2f "%(SumADC_Vinv))



        rawIinv = ((SumADC_Iinv*5000.00)/4096) # rawIinv
        rawIinv = float(format(rawIinv,'.0f'))
        print("     rawIinv = %2.2f mV."%(rawIinv))
        rawIinv = int(rawIinv)
        #print'print==========',rawIinv
        

        
        rawVinv = (SumADC_Vinv*5000.00)/4096 # rawVinv
        rawVinv = float(format(rawVinv,'.0f'))
        
        print("     rawVinv = %2.0f mV."%(rawVinv))

        
        #if((rawIinv >= 8) & (rawIinv < 16)):
        #    Iinv = (-(0.0019)*(rawIinv)*(rawIinv)) + (0.1074*rawIinv) - 0.7407
        #    Iinv = float(format(Iinv,'.1f'))
        #    if(Iinv <= 0):
        #        Iinv = 0.0
            
        #elif(rawIinv >= 16):
        #    Iinv = (0.0333*rawIinv) - 0.0667
        #    Iinv = float(format(Iinv,'.1f'))
        #    if(Iinv <= 0):
        #        Iinv = 0.0

        if(rawIinv < 17):
            Iinv = 0.0
            
        elif((rawIinv >= 17) & (rawIinv < 70)):
            Iinv = ((-0.00007)*rawIinv*rawIinv) +(0.0177*rawIinv) - 0.1695
            Iinv = float(format(Iinv,'.2f'))
            Iinv = int(Iinv * 10)
            Iinv = Iinv /10.00
            
            if(Iinv <= 0):
                Iinv = 0.0
            if(Iinv >= 0.3 ) & (Iinv <= 0.6):
                Iinv = Iinv + 0.04
        elif(rawIinv >= 70):
            Iinv = (0.0075*rawIinv) + 0.2307
            Iinv = (Iinv*1.0583)-0.0235   #cal to power meter
            Iinv = float(format(Iinv,'.2f'))
            #Iinv = int(Iinv * 10)
            #Iinv = Iinv /10.00
            if(Iinv <= 0):
                Iinv = 0.0
                
        

        if(rawVinv < 50):
            Vinv = 0.0   
        elif((rawVinv >= 50.00) & (rawVinv < 600.00)):
            Vinv = (rawVinv * 0.35)
            Vinv = float(format(Vinv,'.2f'))
        elif((rawVinv >= 600.00) & (rawVinv < 650.00)):
            Vinv = (rawVinv * ConstanceVinv1)+199.5
            Vinv = float(format(Vinv,'.2f'))
        




        PowerAC = (Iinv*Vinv)*0.75
        PowerAC = float(format(PowerAC,'.2f'))
        print("     PowerAC = %2.2f W."%(PowerAC))
        print("     Vinv = %2.2f V."%(Vinv))
        print("     Iinv = %2.2f A."%(Iinv))

        #time.sleep(5)
        
    except Exception:
        print '\r'
        print '     ------------------------- Error Inverter function ---------------------'

        #time.sleep(1)


    #------------------------------------------------------------#
    #---------------------- Charger function --------------------#
    #------------------------------------------------------------#
    try:
        print '     --------------------------------------------------------------------'
        print '     ------------------- Working on Charger Function --------------------'
        print '     --------------------------------------------------------------------'
        adc_Icharger = 0.0
        SumADC_Icharger = 0.0
        rawIcharger = 0.0
        Icharger = 0.0
        IchargerP3 = 0.0
        MultiplyIcharger = 0.9195 #CT1DC
        MinusIcharger = 0.1424    #CT1DC
      
        rawIcharger = ReadIdc(1) # rawIcharger ADC 1.1

        for i in range(0,SamplingDC):
            try:
                
                adc_Icharger = adc_raed1(1)   # read ADC Icharger
                SumADC_Icharger = SumADC_Icharger + adc_Icharger
            except Exception:
                print '     Error for SamplingDC Charger'


        SumADC_Icharger = SumADC_Icharger / SamplingDC
        SumADC_Icharger = float(format(SumADC_Icharger,'.0f'))
        print("     ADC Icharger = %2.2f "%(SumADC_Icharger))
        rawIcharger = (SumADC_Icharger*5.00)/4096 # rawIpv
        rawIcharger = convert2dot(rawIcharger,3)
        #rawIcharger = float(format(rawIcharger,'.3f'))
        print'     rawIcharger = ',rawIcharger,'V.'
        #print("     rawIcharger = %2.3f V."%(rawIcharger))

        

        if(rawIcharger >= 0.08):
            Icharger = ((rawIcharger*15.654)-1.4445)
            Icharger = convert2dot(Icharger,2)

            if(Icharger<0):
                Icharger = 0.0

        elif(rawIcharger <  0.08):
            Icharger = 0.0

        print'     Icharger = ',Icharger,'A.'
        #print("     Icharger = %2.2f A."%(Icharger))        
        #time.sleep(5)
        
    except Exception:
        print '\r'
        print '     ------------------------- Error Charger function ---------------------'
        #time.sleep(1)






    #------------------------------------------------------------#
    #-----------------------  User function ---------------------#
    #------------------------------------------------------------#
    try:
        print '     --------------------------------------------------------------------'
        print '     ---------------------   Working on User function  ------------------'
        print '     --------------------------------------------------------------------'

        SumADC_User = 0.0
        rawUser = 0.0

        for i in range(0,SamplingUser):
            try:
                adc_User = adc_raed0(4)# # read ADC Temp1

                SumADC_User = SumADC_User + adc_User
            
            except Exception:
                print '     Error for SamplingUser'


        SumADC_User = SumADC_User / SamplingUser
        print("     ADC User = %2.4f "%(SumADC_User))

        rawVuser = (SumADC_User*5000.00)/4096 # rawUser
        rawVuser = float(format(rawVuser,'.2f'))
        print("     rawVuser = %2.2f mV."%(rawVuser))
        IrrSTL = rawVuser * 46.6#46600
        IrrSTL = IrrSTL * 0.802518
        IrrSTL = IrrSTL * 0.977867
        IrrSTL = float(format(IrrSTL,'.2f'))
        print("     IrrSTL = %2.2f w/m2."%(IrrSTL))
        

        #time.sleep(3)

    except Exception:
        print '\r'
        print '     ------------------------- Error User function ----------------------'

        #time.sleep(1)

    try:
        statusbatt = check_Batt(percent_batt)
        
        #time.sleep(1)

    except Exception:
        print '\r'
        print '     ------------------------- Error Monitoring Batt function ----------------------'
        #time.sleep(1)          

    try:
        print '     --------------------------------------------------------------------'
        print '     ------------------- Check Monitoring Function ----------------------'
        print '     --------------------------------------------------------------------'
  
        CheckIrr = False
        CheckIrr = check_irr(Irr,200)#Irr,check irr
        #CheckIrr = True
        if(CheckIrr):
            CheckPV = check_PV(60,16,Vpv,Ipv) #VpvMAX,IpvMAX,Vpv,Ipv
            if(CheckPV):
                CheckINV = check_Inverter(Vinv,Iinv) #Vinv,Iinv
                if(~CheckINV):
                    GPIO.output(29,GPIO.LOW) #-------red off led inv
                    GPIO.output(31,GPIO.HIGH) #-------green on led inv
                    CheckCharger = check_charger(Icharger,Ipv,Vbatt,VbattMAX,VbattMIN,Iinv,str_status_fan,percent_batt)#(Icharger,Ipv,Vbatt,VbattMAX,VbattMIN,Iinverter,str_status_fan,percent_batt)
  
        else:
            CheckPV = check_PV(60,16,Vpv,Ipv) #VpvMAX,IpvMAX,Vpv,Ipv
            if(CheckPV):
                print '     * Fault alarm light sensor'

        
        #time.sleep(1)

    

    except Exception:
        print '\r'
        print '     ------------------------- %Error Monitoring function ----------------------'

        #time.sleep(1)
   
    try:
        now_time=time.strftime('%H%M')
        Now_time = now_time
        print 'Now Time = ',Now_time
        #time.sleep(5)
        if(Now_time == '0900' or Now_time == '1200' or Now_time == '1500'or Now_time == '1800' or check_ram() >= 90 ):
                print ' Time Rebooting Raspberry Pi........'
                time.sleep(1)
                print '9...'
                time.sleep(1)
                print '8...'
                time.sleep(1)
                print '7...'
                time.sleep(1)
                print '6...'
                time.sleep(1)
                print '5...'
                time.sleep(1)
                print '4...'
                time.sleep(1)
                print '3...'
                time.sleep(1)
                print '2...'
                time.sleep(1)
                print '1...'
                time.sleep(2)
                print ' reboot ok.. '
                time.sleep(2)
                os.system('sudo shutdown -r now')
    
    
        url_reboot='http://184.106.153.149/channels/213183/fields/1/last/'
        response_reboot=urllib2.urlopen(url_reboot,timeout=65)
        print 'Server response..' ,response_reboot.getcode()
        if(response_reboot.getcode()==200):
            print 'Check Server Connected...'
            data_reboot=response_reboot.read()
            print 'Check  reboot....:',data_reboot
            data_re=int(data_reboot)
            print 'data_re = ',data_re
            if (data_re==1):
                print ' Rebooting Raspberry Pi........'
                time.sleep(1)
                print '9...'
                time.sleep(1)
                print '8...'
                time.sleep(1)
                print '7...'
                time.sleep(1)
                print '6...'
                time.sleep(1)
                print '5...'
                time.sleep(1)
                print '4...'
                time.sleep(1)
                print '3...'
                time.sleep(1)
                print '2...'
                time.sleep(1)
                print '1...'
                response_reboot=urllib2.urlopen('https://api.thingspeak.com/update?api_key=8KPHETC77J94UE4W&field1=0' , timeout=65)
                time.sleep(2)
                print ' reboot ok.. '
                time.sleep(2)
                os.system('sudo shutdown -r now')
            else:
                print 'No!! Reboot'
    except Exception:
        print' Can not get response....'

    try:

        print '     --------------------------------------------------------------------'
        print '     ---------------- start send data to server function ----------------'
        print '     --------------------------------------------------------------------'

            
        VRbatt1 = 0.0
        VRbatt2 = 0.0
        led_pv = 1
        led_charger = 1
        led_inv = 1
        led_batt = 1
        led_power = 1
        print '     ++++++++++++++++++++++++++++++++++++++++++++++++++'
        print '     VRbatt1=',VRbatt1
        print '     VRbatt2=',VRbatt2
        print '     led PV=', led_pv
        print '     led Charger=',led_charger
        print '     led INV=',led_inv
        print '     led Batt=',led_batt
        print '     led Power=',led_power


           
        #time.sleep(1)
        str_send_url = 'http://www.thaisolarmonitor.com/getmydata/savedataonline.ashx?sn='+str(getserialCPU())+'&t1='+str(TempPV)+'&t1r='+str(rawTempPV)        +'&t2='+str(TempAMB)+'&t2r='+str(rawTempAMB)+'&t3='+str(TempBox)+'&t3r='+str(rawTemp3)+'&t4='+str(getTemp())+'&lx='+str(Irr)     +'&lxr='+str(rawLight)+'&vdc1='+str(Vpv)+'&Vpv_raw='+str(rawVpv)+'&vac='+str(Vinv)+'&Vinv_raw='+str(rawVinv)+'&ctdcpv='+str(Ipv)+'&Ipv_raw='+str(rawIpv)+'&ctac='+str(Iinv)+'&Iinv_raw='+str(rawIinv)+'&vdc2='+str(Vbatt)+'&Vbatt_raw='+str(rawVbatt)       +'&ctdc='+str(Ibatt)+'&Ibatt_raw='+str(rawIbatt)+'&vbatt1='+str(VRbatt1)+'&VRbatt1_raw='+str(VRbatt1)+'&vbatt2='+str(VRbatt2)+'&VRbatt2_raw='+str(VRbatt2)+'&Icharger='+str(Icharger)+'&Icharger_raw='+str(rawIcharger)       +'&ledpv='+str(led_pv)+'&ledcharger='+str(led_charger)+'&ledinv='+str(led_inv)+'&ledbatt='+str(led_batt)+'&ledpower='+str(led_power)+'&time='+time.strftime('%Y%m%d%H%M%S')+'  '
        print '     str_send_url=',str_send_url


        #+'&statusBatt='+str(check_BattCharg[0])+','+str(check_BattCharg[1])+','+str(check_BattCharg[2])+','+str(check_BattCharg[3])
        response=urllib2.urlopen('http://www.thaisolarmonitor.com/getmydata/savedataonline.ashx?sn='+str(getserialCPU())+'&t1='+str(TempPV)+'&t1r='+str(rawTempPV)        +'&t2='+str(TempAMB)+'&t2r='+str(rawTempAMB)+'&t3='+str(TempBox)+'&t3r='+str(rawTemp3)+'&t4='+str(getTemp())+'&lx='+str(Irr)     +'&lxr='+str(rawLight)+'&vdc1='+str(Vpv)+'&Vpv_raw='+str(rawVpv)+'&vac='+str(Vinv)+'&Vinv_raw='+str(rawVinv)+'&ctdcpv='+str(Ipv)+'&Ipv_raw='+str(rawIpv)+'&ctac='+str(Iinv)+'&Iinv_raw='+str(rawIinv)+'&vdc2='+str(Vbatt)+'&Vbatt_raw='+str(rawVbatt)       +'&ctdc='+str(Ibatt)+'&Ibatt_raw='+str(rawIbatt)+'&vbatt1='+str(VRbatt1)+'&VRbatt1_raw='+str(VRbatt1)+'&vbatt2='+str(VRbatt2)+'&VRbatt2_raw='+str(VRbatt2)+'&Icharger='+str(Icharger)+'&Icharger_raw='+str(rawIcharger)       +'&ledpv='+str(led_pv)+'&ledcharger='+str(led_charger)+'&ledinv='+str(led_inv)+'&ledbatt='+str(led_batt)+'&ledpower='+str(led_power)+'&time='+time.strftime('%Y%m%d%H%M%S')+'  ',timeout=65)
        #'&statusBatt='+str(check_BattCharg[0])+','+str(check_BattCharg[1])+','+str(check_BattCharg[2])+','+str(check_BattCharg[3])+
        time.sleep (5)
        print '     send Data Querystring '

        print response.getcode()
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

  
    print   '       datat save flagedata  online / offline ', flagedata



    try:
    #-----------------  INSERT DATA SQLite  -----------------------------
        VRbatt1 = 0.0
        VRbatt2 = 0.0
        print '     INSERT DATA SOLAR ',time.strftime('%Y/%d/%m %H:%M:%S')
        print '     data save  online [0 online / 1  offline] ',flagedata
        #ser.write('Time')
        #ser.write('\r\n')
        #time.sleep(0.5)
        uart_time1 = ser.readline()
        print uart_time1
        time.sleep(0.5)
        if(uart_time1[0] == 'T'):
            print "OK Time"
            uart_time = uart_time1[1:15]
            print uart_time
        time.sleep(0.5)
        #uart_time = time.strftime('%Y%d%m%H%M%S')
        #ser.write("     -->> INSERT INTO datasolar  VALUES ("+str(datetime)+","+str(TempPV)+","+str(TempAMB)+","+str(TempBox)+","'0.0'","+str(Irr)+","+str(Lux)+","+str(Vinv) +","+str(Vpv)+","+str(Vbatt)+","+str(Iinv)+","+str(Ipv)+","+str(Ibatt)+","+str(Icharger)+","'0.0'","'0.0'","+str(percent_batt)+","+str(datetime)+","+str(flagedata)+","+str(rawTempPV)+","+str(rawTempAMB)+","'0.0'","+str(rawLight)+","+str(rawVinv)+","+str(rawVpv)+","+str(rawVbatt)+","+str(rawIinv)+","+str(rawIpv)+","+str(rawIbatt)+","+str(rawIcharger)+","+str(VRbatt1)+","+str(VRbatt2)+"); ")
        #ser.write('\r\n')
        print "     -->> INSERT INTO datasolar1  VALUES ("+str(uart_time)+","+str(TempPV)+","+str(TempAMB)+","+str(TempBox)+","+str(getTemp())+","+str(Irr)+","+str(Lux)+","+str(Vinv) +","+str(Vpv)+","+str(Vbatt)+","+str(Iinv)+","+str(Ipv)+","+str(Ibatt)+","+str(Icharger)+","'0.0'","+str(statusbatt)+","+str(percent_batt)+","+str(uart_time)+","+str(flagedata)+","+str(IrrSTL)+","+str(rawTempAMB)+","+str(check_ram())+","+str(rawLight)+","+str(rawVinv)+","+str(rawVpv)+","+str(rawVbatt)+","+str(rawIinv)+","+str(rawIpv)+","+str(rawIbatt)+","+str(rawIcharger)+","+str(VRbatt1)+","+str(VRbatt2)+"); "


        dbconnect2 = sqlite3.connect("SolarLoggerNew.db");            
        dbconnect2.row_factory = sqlite3.Row;
        cursor2 = dbconnect2.cursor();
        cursor2.execute("INSERT INTO datasolar1  VALUES ("+str(uart_time)+","+str(TempPV)+","+str(TempAMB)+","+str(TempBox)+","+str(getTemp())+","+str(Irr)+","+str(Lux)+","+str(Vinv) +","+str(Vpv)+","+str(Vbatt)+","+str(Iinv)+","+str(Ipv)+","+str(Ibatt)+","+str(Icharger)+","'0.0'","+str(statusbatt)+","+str(percent_batt)+","+str(uart_time)+","+str(flagedata)+","+str(IrrSTL)+","+str(rawTempAMB)+","+str(check_ram())+","+str(rawLight)+","+str(rawVinv)+","+str(rawVpv)+","+str(rawVbatt)+","+str(rawIinv)+","+str(rawIpv)+","+str(rawIbatt)+","+str(rawIcharger)+","+str(VRbatt1)+","+str(VRbatt2)+");");
        dbconnect2.commit();
        print '     INSERT DATA SOLAR SQLite  OK. '

        dbconnect2.close();
        #time.sleep(1)
        
    except Exception:
        print '     connect database -->sqllit insert  err'
        #time.sleep(1)


    
            

    #ser.write(str(Exception.message))
    #ser.write('\r\n')
    #time.sleep(1)

 
    """except Exception:
        print '     connect database -->sqllit insert  err'
        ser.write(str(Exception.message))
    ser.write('\r\n')
    """

    
#    print '     Ibatt =', Ibatt,'A.'
#    print '     Ipv =', Ipv,'A.'
#    print '     Icharger =', Icharger,'A.'
    time.sleep(10)
    
    print '**********************************************************'
    print '***********************  End Loop  ***********************'
    print '**********************************************************'
    print "\r"
    print "\r"
    print "\r"

    
        
            

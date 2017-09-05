import os
import sqlite3
import urllib2
import time

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


conn = sqlite3.connect('SolarLoggerNew.db')
c = conn.cursor()
getserialCPU()

def test():
    str_send_url1 = 'http://www.thaisolarmonitor.com/getmydata/backupdataonline.ashx?sn=000000004fc3186c&t1='+str(20)+'&t1r='+str(25)+'&t2='+str(30)+'&t2r='+str(0.6)+'&t3='+str(0.7)+'&t3r='+str(0.8)+'&t4='+str(0.9)+'&lx='+str(1000)+'&lxr='+str(2.5)+'&vdc1='+str(50)+'&Vpv_raw='+str(55)+'&vac='+str(2.5)+'&Vinv_raw='+str(2.5)+'&ctdcpv='+str(2)+'&Ipv_raw='+str(1)+'&ctac='+str(0)+'&Iinv_raw='+str(10)+'&vdc2='+str(11)+'&Vbatt_raw='+str(12)+'&ctdc='+str(13)+'&Ibatt_raw='+str(12)+'&vbatt1='+str(48)+'&VRbatt1_raw='+str(0)+'&vbatt2='+str(0)+'&VRbatt2_raw='+str(0)+'&Icharger='+str(0)+'&Icharger_raw='+str(0)+'&time='+str(20170320103550)+' '
    response=urllib2.urlopen(str_send_url1,timeout=65)
    print ( response.getcode() )

str_send_url1 = 'http://www.thaisolarmonitor.com/getmydata/backupdataonline.ashx?sn=000000004fc3186c&t1='+str(20)+'&t1r='+str(25)+'&t2='+str(30)+'&t2r='+str(0.6)+'&t3='+str(0.7)+'&t3r='+str(0.8)+'&t4='+str(0.9)+'&lx='+str(1000)+'&lxr='+str(2.5)+'&vdc1='+str(50)+'&Vpv_raw='+str(55)+'&vac='+str(2.5)+'&Vinv_raw='+str(2.5)+'&ctdcpv='+str(2)+'&Ipv_raw='+str(1)+'&ctac='+str(0)+'&Iinv_raw='+str(10)+'&vdc2='+str(11)+'&Vbatt_raw='+str(12)+'&ctdc='+str(13)+'&Ibatt_raw='+str(12)+'&vbatt1='+str(48)+'&VRbatt1_raw='+str(0)+'&vbatt2='+str(0)+'&VRbatt2_raw='+str(0)+'&Icharger='+str(0)+'&Icharger_raw='+str(0)+'&time='+str(20170320103550)+' '

def read_from_db():
    try:
        c.execute('SELECT * FROM datasolar1')
        for row in c.fetchall():
            if(row[18] == '1'):
                print(row[18])
                print(row)
                #str_send_url = '27.254.144.134/getmydata/savedataonline.ashx?sn='+str(getserialCPU())+'&t1='+str(TempPV)+'&t1r='+str(rawTempPV)        +'&t2='+str(TempAMB)+'&t2r='+str(rawTempAMB)+'&t3='+str(TempBox)+'&t3r='+str(rawTemp3)+'&t4='+str(getTemp())+'&lx='+str(Irr)     +'&lxr='+str(rawLight)+'&vdc1='+str(Vpv)+'&Vpv_raw='+str(rawVpv)+'&vac='+str(Vinv)+'&Vinv_raw='+str(rawVinv)+'&ctdcpv='+str(Ipv)+'&Ipv_raw='+str(rawIpv)+'&ctac='+str(Iinv)+'&Iinv_raw='+str(rawIinv)+'&vdc2='+str(Vbatt)+'&Vbatt_raw='+str(rawVbatt)       +'&ctdc='+str(Ibatt)+'&Ibatt_raw='+str(rawIbatt)+'&vbatt1='+str(VRbatt1)+'&VRbatt1_raw='+str(VRbatt1)+'&vbatt2='+str(VRbatt2)+'&VRbatt2_raw='+str(VRbatt2)+'&Icharger='+str(Icharger)+'&Icharger_raw='+str(rawIcharger)       +'&ledpv='+str(led_pv)+'&ledcharger='+str(led_charger)+'&ledinv='+str(led_inv)+'&ledbatt='+str(led_batt)+'&ledpower='+str(led_power)+'&time='+time.strftime('%Y%m%d%H%M%S')+'  '
                str_send_url = 'http://www.thaisolarmonitor.com/getmydata/backupdataonline.ashx?sn='+str(getserialCPU())+'&t1='+str(row[1])+'&t1r='+str(row[19])+'&t2='+str(row[2])+'&t2r='+str(row[20])+'&t3='+str(row[3])+'&t3r='+str(row[21])+'&t4='+str(row[4])+'&lx='+str(row[5])+'&lxr='+str(row[22])+'&vdc1='+str(row[8])+'&Vpv_raw='+str(row[24])+'&vac='+str(row[7])+'&Vinv_raw='+str(row[23])+'&ctdcpv='+str(row[11])+'&Ipv_raw='+str(row[27])+'&ctac='+str(row[10])+'&Iinv_raw='+str(row[26])+'&vdc2='+str(row[9])+'&Vbatt_raw='+str(row[25])+'&ctdc='+str(row[12])+'&Ibatt_raw='+str(row[28])+'&vbatt1='+str(row[30])+'&VRbatt1_raw='+str(row[30])+'&vbatt2='+str(row[31])+'&VRbatt2_raw='+str(row[31])+'&Icharger='+str(row[13])+'&Icharger_raw='+str(row[29])+'&time='+str(row[0])+' '
                print '     str_send_url=',str_send_url
                response=urllib2.urlopen(str_send_url,timeout=65)
                print  (response.getcode()) 
                time.sleep(5)
                #print '     send Data Querystring '
                #print  response.getcode() 
                
                if(response.getcode() == 200):
                    try:
                        print("response == 200")
                        with conn:   
                            c.execute("UPDATE datasolar1 SET flage='0' WHERE flage='1'")
                            #c.execute("UPDATE datasolar1 SET flage='1' WHERE flage='0'")
                            print '     update flag to 0 insert SQLite  OK. '
                    except Exception:
                        print '   Dont update flage'
                

    except Exception:
            print '   Dont select DATABASE'
            
read_from_db()
c.close()
conn.close()

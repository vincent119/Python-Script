#!/usr/bin/env python
#coding=utf8

import sys
import os
import re
import math
from optparse import OptionParser
from pysnmp.entity.rfc3413.oneliner import cmdgen
#
#     Script by Vincent Yu
#     Created date 20160929
#
#     T3510 溫度感測器 溫度檢查 for Nagios
#   http://www.cometsystem.com/products/reg-T3510
#

def validip(ip):
    return ip.count('.') == 3 and  all(0<=int(num)<256 for num in ip.rstrip().split('.'))

def is_number(s):
    try:
        float(s) # for int, long and float
    except ValueError:
        try:
            complex(s) # for complex
        except ValueError:
            return False
    return True

def options():
    #usage = "usage: %prog [options] arg1 arg2"
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-H","--host", action="store", type="string", default="localhost",dest="IP",help="IP only")
    parser.add_option('-v',"--version", type="int",dest="VERSION",default="2",help="V1 or V2")
    parser.add_option('-p',"--port", type="int", default=161,dest="PORT",help="default port 161")
    parser.add_option('-c',"--community", type="string",dest="COMMUNITY",help="")
    parser.add_option('-C',"--critical", type="int",dest="CRITICAL",help="")
    parser.add_option('-W','--warning', type="int",dest="WARN",help="")
   
   
    return parser.parse_args()


def threshold_vlaue(ip,port,version,communtiy,critical,warning):
    SNMP_HOST=ip
    SNMP_PORT=port
    SNMP_COMMUNITY=communtiy
    if version == 1:
        SNMP_VERSION=0
    else:
        SNMP_VERSION=1
    CRITICAL=critical
    WARNING=warning
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
    cmdgen.CommunityData(SNMP_COMMUNITY, mpModel=SNMP_VERSION),cmdgen.UdpTransportTarget((SNMP_HOST, SNMP_PORT)),'1.3.6.1.4.1.22626.1.2.1.1.0')
    for name, val in varBinds:
        TempValue=val.prettyPrint()
    
    if  CRITICAL and WARNING:
        if float(TempValue) >= CRITICAL:
	   print "CRITICAL 溫度超過 %s |temperature=%s"  %(TempValue,TempValue)
           sys.exit(2)
        elif float(TempValue) > WARNING:
	   print "WARNING 溫度超過 %s |temperature=%s"  %(TempValue,TempValue)
	   sys.exit(1)
	else:
	   print "OK 溫度%s |temperature=%s"  %(TempValue,TempValue)
	   sys.exit(0)
    else:
	print "現在溫度 %s 度" %(TempValue)    
              

def main():
    if len(sys.argv) == 1:
        print "ERROR! Please enter a key......"
        print "Example .py -H IPADDRESS -v 2 -p 161"
    elif len(sys.argv) >= 4:
        ip = opts.IP
        port = opts.PORT
 	version = opts.VERSION
	communtiy =  opts.COMMUNITY
        critical = opts.CRITICAL
        warning = opts.WARN
        if validip(ip) == True:
	    if opts.VERSION and opts.COMMUNITY:
 	        threshold_vlaue(ip,port,version,communtiy,critical,warning)
            else:
                print "check SNMP Version or snmp community string!!!!"
       	else:
            print "錯誤IP格式!!"

if __name__ == "__main__":
    (opts, args) = options()
    main()

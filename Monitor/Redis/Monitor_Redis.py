#!/usr/bin/env python
#coding=utf8

import sys
import os
import re
from optparse import OptionParser
from redis import ConnectionError
import redis
#
#     Script by Vincent Yu
#     Created date 10151012
#	  Script for Nagios
#
#     key used_memory , used_cpu_sys , used_memory_human
#
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
    parser.add_option('--host', action="store", type="string", default="localhost",dest="IP",help="IP only")
    parser.add_option("--key",action="store", type="string",default="used_memory",dest="KEY",help="key = used_memory or connected_clients")
    parser.add_option("--port", type="int", default=6379,dest="PORT",help="default port 6379")
    parser.add_option("--threshold", type="int",dest="THRES",help="value is 10 ~ 100")
    return parser.parse_args()

class GetRedisStatus():
    def __init__(self):
        self.val = {}
    def check(self,ip,port):
        try:
            self.redis = redis.Redis(ip, port, password=None)
        except:
            raise Exception, 'Plugin needs the redis module'

    def extract(self, key):
        info = self.redis.info()
        try:
            if key in info:
                self.val[key] = info[key]
            return self.val[key]
        except:
            raise Exception, 'ERROR info not include this key!'
    def extract_get(self, key):
        get = self.redis.config_get(pattern=key)
        try:
            if key in get:
                self.val[key] = get[key]
            return self.val[key]
        except:
            raise Exception, 'ERROR info not include this key!'

def isredis_available(ip):
    rs = redis.Redis(ip)
    try:
        rs.get(None)  # getting None returns None or throws an exception
    except (redis.exceptions.ConnectionError, 
            redis.exceptions.BusyLoadingError):
        return False
    return True

def threshold_vlaue(ip,port,key,threshold):
    connectRedis = GetRedisStatus()
    connectRedis.check(ip,port)  
    if key == "used_memory":
        selkey = connectRedis.extract(key)
        key2 = "maxmemory"
        confkey = connectRedis.extract_get(key2)
        thres= float(float(threshold)/float(100))        
        result = int(float(confkey)*float(thres))
        if result <= selkey:
            threshold = str(threshold)+"%"
            print "CRITICAL |超出 %r memory_use %s"  %(threshold,selkey)
            sys.exit(2)  
        else:
           print "OK |memory_use %s MB maxmemory %s MB"  %(int(selkey)/1024/1024,int(confkey)/1024/1024)
           sys.exit(0)
    elif key == "connected_clients":
        selkey = connectRedis.extract(key)
        key2 = "maxclients"
        confkey = connectRedis.extract_get(key2)
        thres= float(float(threshold)/float(100))
        result = int(float(confkey)*float(thres))
        if result <= selkey:
            threshold = str(threshold)+"%"
            print "CRITICAL |超出 %r 連線數: %s"  %(threshold,selkey)
             #printf("CRITICAL |超出 %s % memory_use %s",threshold,selkey)
            sys.exit(2)
        else:
           print "OK |連線數: %s 最大連線數: %s"  %(selkey,confkey)
           sys.exit(0)
              

def main():
    if len(sys.argv) == 1:
        print "ERROR! Please enter a key......"
        print "Example .py IPADDRESS `"
    elif len(sys.argv) >= 2:
        ip = opts.IP
        port = opts.PORT
        key = opts.KEY
        threshold = opts.THRES
        if validip(ip) == True:
            if isredis_available(ip) != False:
                if opts.KEY and opts.THRES:
                    threshold_vlaue(ip,port,key,threshold)
                elif opts.KEY:
                    connectRedis = GetRedisStatus()
                    connectRedis.check(ip,port)
                    show=str((int(connectRedis.extract(key))/1024/1024))+"MB"
                    print show
                    sys.exit(0)
            else:
                print "CRITICAL - Can't connect %s" %ip
                sys.exit(3)
        else:
            print "錯誤IP格式!!"

if __name__ == "__main__":
    (opts, args) = options()
    main()

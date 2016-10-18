#!/usr/bin/env python
#coding=utf8

import smtplib
import HTML
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import subprocess
import sys
import os
import time
import datetime
from time import strftime
from datetime import datetime, timedelta
from pyhtml import *

# 備份檔案路徑
bkDir='/Rmanbackup1/edb'
# postgres 執行檔路徑
pgPath='/edb/9.5AS/bin'
domainName='domain.com.tw'
superUser='enterprisedb'
##################
mailFROM = 'mailfrom@domain.com.tw'
mailTO = ['user1@domain.com.tw','user2@domain.com.tw']
mailSUBJECT = u'EDB backup Report'
SERVER = 'localhost'
##################
DBlist = [['db-01','postgres'],['db-02','postgres'],['edb-03','postgres']]
Status=[]

def RunCmd(cmdarg):
   cmd=cmdarg
   retcode = subprocess.call(cmd, shell=True)
   if retcode != 0: 
       sys.exit(retcode)
   else:
       return retcode

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s %s" % (num, 'Yi', suffix)

def genhtmlreport(today,enDdate,Status):
    starttime=today
    endtime=enDdate
    TEXT ='<!doctype html public '"-//w3c//dtd html 4.0 transitional//en"'><html><head><meta http-equiv='"Content-Type"' content='"text/html; charset=utf-8"'></head><body> <style>table {width:100%;}table, th, td {border: 1px solid black;border-collapse: collapse;}th, td {padding: 5px;text-align: left;}table#t01 tr:nth-child(even) {background-color: #eee;}table#t01 tr:nth-child(odd) {background-color:#fff;}table#t01 th {background-color: green;color: white;}</style></head><body>'
    TEXT=TEXT+'<table id="t01">'+'Start Time: '+today+'</p>'
    htmlcode = HTML.table(Status, header_row=['Server Name','DB Name','Run Time','DB Size'])
    TEXT=TEXT+htmlcode+'</p>'+'End Time: '+enDdate+'</table></body></html>'
    sendmail(TEXT)

def sendmail(RepHtml):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = mailSUBJECT
    msg['From'] = mailFROM
    msg['To'] = ', '.join(mailTO)
    part = MIMEText(RepHtml, 'html', 'utf-8')
    msg.attach(part)

    server = smtplib.SMTP(SERVER)
    server.sendmail(mailFROM, mailTO, msg.as_string().encode('ascii'))
    server.quit()
 

def tr(serverdata,htmdata):
    fielddata=htmdata
    fieldserver=serverdata
    Table="<tr>"
    for field in serverdata:
        Table=Table+"<td>"+fielddata[fieldserver]+"</td>"
    Table=Table+"</tr>"
    return Table 

def backupStart():
    today=(datetime.now() + timedelta(days=0)).strftime('%Y-%m-%dT%H:%M')
    for row in DBlist:
      dbserver=row[0]
      dbname=row[1]
      dirpath=bkDir+'/'+dbserver
      if os.path.exists(dirpath) == False:
          os.mkdir(dirpath)  
        
      filepath=bkDir+'/'+dbserver+'/'+dbname+'.gz'
      cmd=pgPath+'/pg_dump -h '+dbserver+'.'+domainName+' -U '+superUser+' -d '+dbname+' | gzip > ' +filepath
      start = time.time()
      RunCmd(cmd)
      roundtrip = (time.time() - start)
      Status.append([dbserver,dbname,format(roundtrip,'.2f'),str(sizeof_fmt(os.path.getsize(filepath)))])
     
    enDdate=(datetime.now() + timedelta(days=0)).strftime('%Y-%m-%dT%H:%M')
    genhtmlreport(today,enDdate,Status)



if __name__ == "__main__":
  backupStart()

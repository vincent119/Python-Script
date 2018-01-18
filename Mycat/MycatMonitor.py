#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Monitor Maycat status """


import os,sys
import mysql.connector
from mysql.connector import errorcode
from optparse import OptionParser
import itertools
filepath='/tmp/heartbeat2.txt'

def options():
    #usage = "usage: %prog [options] arg1 arg2"
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option('--C', action="store", type="string",dest="connection",help="query mycat connect count")
    parser.add_option('--Q', action="store", type="string",dest="heartbeat",help="query mycat heartbeat")
    return parser.parse_args()

config = {
  'user': '000',
  'password': '0000',
  'host': '1.1.1.1',
  'database': '000',
  'port': '3306',
  'connection_timeout':10,
  'raise_on_warnings': True,
}
def writeFile(filename,PStr):
    filehandle = open(filename,'w')
    filehandle.write(PStr)
    #print PStr
    filehandle.close()

class MycatConnect():
  def __init__(self):
    try:
      self.conn=mysql.connector.connect(**config)
      self.cur = self.conn.cursor()
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
	print("Database does not exist")
      else:
	print(err)
  def DBQuery(self,sql):
    self.cur.execute(sql)
    return self.cur.fetchall()
  def DBQueryConnect(self):
    sql='show @@connection'
    self.cur.execute(sql)
    return len(self.cur.fetchall())
  def DBQueryHearbeat(self):
    sql='show @@heartbeat'
    self.cur.execute(sql)
    return list(self.cur.fetchall())
  def DBQueryBackend(self):
    sql='show @@backend'
    self.cur.execute(sql)
    return list(self.cur.fetchall())
  def close(self):
    if self.conn:
      self.conn.close()	
  def __exit__(self, exc_type, exc_val, exc_tb):
    if self.conn:
      self.conn.close()	
      
def BackedQuery(StrResult):
  ListDB=[]
  for p in range(len(StrResult)):
    StrList=list(StrResult[p])
    ListDB.append("".join(str(StrList[12])))
  ListDB.sort()
  ListBB=[]
  for k, g in itertools.groupby(ListDB):
    intC= sum(1 for x in g)
    ListBB.append( [k, str(intC)] )
  sys.stdout=open(filepath,"a")
  print ("<--table DBnode starts-->")
  print ("DB_NAME DB_CONNECT")
  for x in range(len(ListBB)):
    print "".join(str(ListBB[x][0])),"".join(str(ListBB[x][1]))
  print ("<--table DBnode ends-->")
  sys.stdout.close()

def main():
  connectMycat = MycatConnect()
  Str=connectMycat.DBQueryHearbeat()
  sys.stdout=open(filepath,"w")
  print ("<--table heartbeat starts-->")
  print ("NAME HOST RS_CODE")
  for p in range(len(Str)):
    StrList=list(Str[p])
    print "".join(str(StrList[0])),"".join(str(StrList[2])),"".join(str(StrList[5]))
  print ("<--table heartbeat ends-->")
  sys.stdout.close()
  
  Str=connectMycat.DBQueryConnect()
  sys.stdout=open(filepath,"a")
  print ("<--table connection starts-->")
  print ("NAME COUNT")
  print "Max_Count",Str
  print ("<--table connection ends-->")
  sys.stdout.close()
  
  
  Str=connectMycat.DBQueryBackend()
  BackedQuery(Str)
  ''' connection close '''
  connectMycat.close()
  reload(sys)
  sys.setdefaultencoding('utf-8')

  
if __name__ == "__main__":
  (opts, args) = options()
  #reload(sys)
  #sys.setdefaultencoding('utf-8')
  main()


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os,sys
from pathlib import Path
import mysql.connector
import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
from mysql.connector import errorcode
from optparse import OptionParser
import itertools
import json
import yaml
import time
from datetime import timedelta,datetime
import telepot
import HTML,re

config_yaml_path = '/opt/APP/APM_Script/check_mysql_slave2/check_mysql_slave.yaml'
logPath='/opt/logs/check_mysql_slave'
logConf='/opt/APP/APM_Script/check_mysql_slave/logging.yaml'
MasterDelayCount = 5
DBconnect_timeout = 10

def options():
    #usage = "usage: %prog [options] arg1 arg2"
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option('--C', action="store", type="string",dest="connection",help="query mycat connect count")
    parser.add_option('--Q', action="store", type="string",dest="heartbeat",help="query mycat heartbeat")
    return parser.parse_args()
    
'''config = {
  'user': 'S4iq0',
  'password': 'bQ68#y2',
  'host': '172.29.169.29',
  'database': 'boss',
  'port': '9066',
  'connection_timeout':10,
  'raise_on_warnings': True,
}'''
class switch(object):
  def __init__(self, value):
    self.value = value
    self.fall = False

  def __iter__(self):
    """Return the match method once, then stop"""
    yield self.match
    raise StopIteration
  def match(self, *args):
    """Indicate whether or not to enter a case suite"""
    if self.fall or not args:
      return True
    elif self.value in args: # changed for v1.5, see below
      self.fall = True
      return True
    else:
      return False
      
def setup_logging(default_path, default_level=logging.INFO, env_key='LOG_CFG'):
 
  """
  | **@author:** Prathyush SP
  | Logging Setup
  """
  path = default_path
  value = os.getenv(env_key, None)
  if value:
    path = value
  if os.path.exists(path):
    with open(path, 'rt') as f:
      try:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
      except Exception as e:
        print(e)
        print('Error in Logging Configuration. Using default configs')
        logging.basicConfig(level=default_level)
  else:
    logging.basicConfig(level=default_level)
    print('Failed to load configuration file. Using default configs')

def fileexists(path):
  try:
    st = os.stat(path)
  except os.error:
    return False
  return True
  
def writeFile(filename,PStr):
    filehandle = open(filename,'w')
    filehandle.write(PStr)
    #print PStr
    filehandle.close()
      
def writeLog(msg,logtype):
  v = logtype.upper()
  for case in switch(v):
    if case('CRITICAL'):
      setup_logging(logConf,logging.CRITICAL)
      logger = logging.getLogger()
      logger.critical(msg)
      break
    if case('ERROR'):
      setup_logging(logConf,logging.ERROR)
      logger = logging.getLogger()
      logger.error(msg)
      break
    if case('WARNING'):
      setup_logging(logConf,logging.WARNING)
      logger = logging.getLogger()
      logger.warning(msg)
      break
    if case('INFO'):
      setup_logging(logConf,logging.INFO)
      logger = logging.getLogger()
      logger.info(msg)
      break
    if case('DEBUG'):
      setup_logging(logConf,logging.DEBUG)
      logger = logging.getLogger()
      logger.debug(msg)
      break
    #if case(): # default, could also just omit condition or 'if True'
    #  print "something else!"
    #  # No need to break here, it'll stop anyway
    
class MycatConnect():
  def __init__(self,dbUser,dbPwd,slaveIP,sport):
    try:
      #self.conn=mysql.connector.connect(**config)
      self.conn=mysql.connector.connect(user=dbUser, password=dbPwd,host=slaveIP,port=sport,database='mysql'\
      ,connect_timeout=DBconnect_timeout)
      self.cur = self.conn.cursor()
    except mysql.connector.Error as err:
      if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
        writeLog('slave IP: '+ slaveIP + " Something is wrong with your user name or password",'error')
      elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
        writeLog('slave IP: '+ slaveIP + " Database does not exist",'error')
      else:
        print(err)
        writeLog('slaveIP ' + err,'error')
  def DBQuery(self):
    sql = 'show slave status'
    self.cur.execute(sql)
    return self.cur.fetchall()
  def close(self):
    if self.conn:
      self.conn.close()	
  def __exit__(self, exc_type, exc_val, exc_tb):
    if self.conn:
      self.conn.close()	

def Convert(string): 
    li = list(string.split(", ")) 
    return li 

def get_yaml_config(path):
  with open(path, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
  return cfg
  
def is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    pass

  try:
    import unicodedata
    unicodedata.numeric(s)
    return True
  except (TypeError, ValueError):
    pass
  
  return False

def is_not_blank(s):
    return bool(s and s.strip())
    
def get_repl_status(dbUser,dbPwd,slaveIP,sPort,serviceName,custName,seqNumber,db_Name):
  quertString = []
  connectMycat = MycatConnect(dbUser,dbPwd,slaveIP,sPort)
  quertString = Convert(json.dumps(connectMycat.DBQuery()[0]))
  '''
  for p in quertString:
    print(p)
  
   Slave_IO_State == column(1)
   Slave_IO_Running == column(10)
   Slave_SQL_Running == column(11)
   Seconds_Behind_Master == column(32)
   quertString ==  column(21)
  '''
  Slave_IO_State = quertString[1] 
  Slave_IO_Running = quertString[10]    
  Slave_SQL_Running = quertString[11]
  Seconds_Behind_Master = quertString[32]
  if (not is_number(Seconds_Behind_Master)) or (not Seconds_Behind_Master):
    Seconds_Behind_Master = 0
    
  Exec_Master_Log_Pos = quertString[21]
  if (Slave_IO_Running != '"Yes"') or (Slave_SQL_Running != '"Yes"') or (Seconds_Behind_Master < MasterDelayCount):
    Slave_IO_State = quertString[0].split("[")[1]
    if Slave_IO_State == '""':
      Slave_IO_State = 'db sync broke down'
    writeLog(serviceName+' '+ slaveIP+' '+Slave_IO_State,'error')
    dictSeq = {}
    dictSeq = {'Slave_IO_Running':Slave_IO_Running,'Slave_SQL_Running':Slave_SQL_Running\
       ,'slaveIP':slaveIP,'Slave_IO_State':Slave_IO_State,'serviceName':serviceName,'db_Name':db_Name,\
       'Seconds_Behind_Master':Seconds_Behind_Master}
    return dictSeq
    
  else:
    messg = custName +' '+ serviceName +' '+slaveIP+ ' Status "Yes" with Slave_IO_Running and Slave_SQL_Running'
    writeLog(messg,'info')
    # dictSeq = {'Slave_IO_Running':Slave_IO_Running,'Slave_SQL_Running':Slave_SQL_Running\
       # ,'slaveIP':slaveIP,'Slave_IO_State':Slave_IO_State,'serviceName':serviceName,'db_Name':db_Name,\
       # 'Seconds_Behind_Master':Seconds_Behind_Master}
    # return dictSeq,False

  ''' connection close '''
  connectMycat.close()
  reload(sys)
  sys.setdefaultencoding('utf-8')  
  
def message_tg(dateTime,dict_obj):
  DATE = dateTime
  msgtmp = ''
  '''
  for cid,keytmp2 in dict_obj.items():
    print(cid)
    print(keytmp2[0]['Seconds_Behind_Master'])
  '''
  for cid,keytmp in dict_obj.items():
    custId = cid
    msg = '''`{CUSTNAME} 数据库主从同步中断 告警`
    时间: {DATETIME}'''.format(CUSTNAME = custId,DATETIME = DATE)
    for keys in keytmp:
      keyCount = keys
      serviceName = keytmp[keys]['serviceName']
      ip = keytmp[keys]['slaveIP']
      slvae_ip_running = keytmp[keys]['Slave_IO_Running']
      slvae_sql_running = keytmp[keys]['Slave_SQL_Running']
      slvae_io_state = keytmp[keys]['Slave_IO_State']
      Seconds_Behind_Master = keytmp[keys]['Seconds_Behind_Master']
      db_Name = keytmp[keys]['db_Name']
      msg1 = '''\n {SEQ}
      名称: {SERVICENAME}
      IP: {SLAVEIP}
      數據庫名稱: {DBNAME}
      IO线程是否启动: {SLAVE_IO_RUNNING}
      SQL線程是否啟動: {SLAVE_SQL_RUNNING}
      主从延迟时间: {Seconds_Behind_Master}
      错误内容: {SLAVE_IO_STATE}
      '''.format(SEQ = 'DB-SLAVE-'+str(keyCount),SERVICENAME = serviceName,SLAVEIP = ip, \
                DBNAME = db_Name,SLAVE_IO_RUNNING = slvae_ip_running, \
                SLAVE_SQL_RUNNING = slvae_sql_running,Seconds_Behind_Master = Seconds_Behind_Master,SLAVE_IO_STATE = slvae_io_state)
      
      msgtmp = msgtmp + msg1
    msg = msg +  msgtmp
  #print(msg)
  bot = telepot.Bot('764708613:AAEu_JDEU6YDoXuXCvsNuYQWLkIUmKUKUtk')
  tgStatus = bot.sendMessage(-1001278170500, text=msg,parse_mode='Markdown' )
  writeLog(tgStatus,'info')

def main():

  read_conf = get_yaml_config(config_yaml_path) 
  k_count = 0
  tg_status = 0
  for k in (read_conf):
    custName = str((list(read_conf)[k_count]))
    for seqDbNumber in (read_conf[k]):
      slaveIP =  read_conf[k][seqDbNumber][0]['slaveIP']
      dbUser = read_conf[k][seqDbNumber][1]['dbUser']
      dbPwd =  read_conf[k][seqDbNumber][2]['dbPwd']
      sPort = read_conf[k][seqDbNumber][3]['port']
      disalbeCheck = read_conf[k][seqDbNumber][4]['disalbe_check']
      serviceName = read_conf[k][seqDbNumber][5]['service_name']
      db_Name = read_conf[k][seqDbNumber][6]['db_Name']
      #if disalbeCheck == True:
      dict1 = {}
      dict2 = {}  
      if disalbeCheck:
        #print (str(custName) + ' : ' + slaveIP + ' stop check status' )
        writeLog(serviceName + ' : ' + slaveIP + ' stop check status','info')
      else:
        tmpdict= get_repl_status(dbUser,dbPwd,slaveIP,sPort,serviceName,custName,seqDbNumber,db_Name)
        if tmpdict != None: 
          dict2[seqDbNumber] = tmpdict
          dateTime =  (datetime.now()).strftime('%Y%m%d-%H%m%S')
          dict1 = {custName:dict2} 
          #if bool(dict1[custName]) and bool(dict1[custName][0]):
            #print(dict1)
          message_tg(dateTime,dict1)
      
    tg_status = tg_status + 1
    k_count = k_count + 1

if __name__ == "__main__":
  (opts, args) = options()
  p = Path(logPath)
  
  if not p.exists():
    os.makedirs(logPath)
    
  main()


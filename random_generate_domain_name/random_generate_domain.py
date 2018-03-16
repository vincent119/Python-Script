# -*- coding: utf-8 -*-


import random
import os
import time

print ('-------------------------')
print ('--- 隨機域名產生器-------')
print ('-------------------------')
chars = int(input('輸入長度: '))
times = int(input('需要產生幾組: '))

d = 'abcdefghijklmnopqrstuvxyz1234567890'
word = ''
letter = ''
filepath='c:\domin_temp\\'
filename=(time.strftime("%Y-%m-%d-%H%M%S", time.localtime()))+'domain_'+str(times)+'.txt'
if not os.path.exists(filepath):
  os.makedirs(filepath)

pfile=filepath + filename
file = open(pfile, 'w', encoding = 'UTF-8')  
while times > 0:
    for i in range(chars):
        letter = d[random.randint(0, len(d) -1)]
        word = word + letter
    genword=word+'.com\n'
    print (genword)
    file.write(genword)
    word = ''
    times -= 1
file.close()
print ('-------------------------')
print ('----------執行完成-------')
print ('-檔案存放在 '+pfile)
print ('-------------------------')
os.system("pause")
	


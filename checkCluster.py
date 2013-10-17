#!/usr/bin/env python
# coding: utf-8

import subprocess
import os
import datetime
import time
import logging
import logging.handlers

HOSTLIST="/root/hostlist"
RESULTFILE="/root/RESULTFILE"
NAME='%s' % os.uname()[1]

#[ACT]か[SBY]かを選択
COMMAND ="/home/swing/sysswitchctl"
TRAPCOMM="/usr/bin/snmptrap -v 1 -c public 192.168.41.214 1.3.6.1.4.1.9999 localhost 6 1 \'\' 1.3.6.1.4.1.9999.1 s \"" 
#秒
SLEEP_TIME=1800

LOGFILE="/root/checkCluster.log"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formater=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
rfh=logging.handlers.RotatingFileHandler(
	filename=LOGFILE,
	maxBytes=500000000,
	backupCount=4
)
rfh.setLevel(logging.DEBUG)
rfh.setFormatter(formater)

logger.addHandler(rfh)

#リモートのホスト名を取得
def gethostname(ip):
	hname ="/usr/bin/rsh " + ip + " hostname"
	out= subprocess.Popen(hname, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
	outResult,errMsg = out.communicate()
	hostnm = outResult.rstrip()

	#判定を行う
        if hostnm is None or hostnm == "":
        	print " Can Not Get Results "+ ip + errMsg
		logger.error("Can Not Get Results "+  errMsg)
	
	return hostnm
	
#結果ファイルを読み込み前回のデータを取得する
def readResultfile() :

	dict={}

	#ファイルが存在しなかったら
	if os.path.exists(RESULTFILE) == False:
		return dict
	f=open(RESULTFILE,'r')
	for line in f:

		#改行を削除
		plainline = line.rstrip()
		if plainline != '':

			itemlist = plainline.split("\t")
			dict[itemlist[1]]=plainline
	f.close()
	return dict


#ファイル読み込み
def readfile() :
	list=[]
	
	#ファイルが存在しなかったら
	if os.path.exists(HOSTLIST) == False:
		return list
	f=open(HOSTLIST,'r')
	for line in f:
                #改行を削除
                plainLine = line.rstrip()
                if plainLine != '':		

			#リストに追加
			list.append( plainLine )
	f.close()
	return list;

#ファイル書き込み
def writeFile(str):

	#ファイルオープン
	f = open(RESULTFILE,'w')
	f.write(str)
	f.close()


logger.info("START")
while 1:
	writestring = ""
	list = readfile()

	for i in range(0, len(list),1):
		
		#RSHでコマンドを実行する
		rshcom ="/usr/bin/rsh " + str(list[i]) + " " + COMMAND
		out= subprocess.Popen(rshcom, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
		outResult,errMsg = out.communicate()
		
		#判定を行う
		if outResult is None or outResult == "":
			print "Can Not Get Result "+ str(list[i]) + errMsg 
			logger.error("Can Not Get Results "+  errMsg)
			continue
		
		print str(list[i]) + outResult

		#ACTかどうか
		if '[ACT]' in outResult:
		
			#結果ファイルを読み込む
			outlist = readResultfile()

			#結果の中にホストが存在することを確認
			if outlist.has_key(str(list[i])):

				#ホストが存在したらステータスを確認する
				oldstatus =outlist[str(list[i])]
				oldlist = oldstatus.split("\t")
				
				#値の数が満たない場合はエラー
				if len(oldlist) < 2:
					logger.error("cannot get last value " + str(list[i]))
					print "cannot get last value " + str(list[i])
					continue
				
				#前回がSBYの場合
				if oldlist[2] == '[SBY]':
					#ホスト名の取得
                                        hostname = gethostname(str(list[i]))	
					
					print " =========" + hostname + " Server Chenged [SBY] -> [ACT] ! ========="
					logger.error("=========" + hostname + " Server Chenged [SBY] -> [ACT] ! =========" )

					##### TRAP出力 #####
					TRAPMSG = TRAPCOMM + " =========" + hostname +" Server Chenged [SBY] -> [ACT] ! =========\""

					out = subprocess.Popen(TRAPMSG,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
					outMsg,errMsg = out.communicate()
					if errMsg != "":
						logger.error("snmptrap send error " + str(list[i]) + hostname + " " + errMsg)
						print str(list[i]) + " snmptrap error " + errMsg
					
				
			#バッファに出力
                       	#現在時間の取得
                       	nowtime=datetime.datetime.now()
                       	nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')
			writestring += nowstr + "\t" + str(list[i]) + "\t" + '[ACT]\n'
				
				
		#SBYの時
		elif '[SBY]' in outResult:
		
			#結果ファイルを読み込む
			outlist = readResultfile()

			#結果の中にホストが存在することを確認
			if outlist.has_key(str(list[i])):
				#ホストが存在したらステータスを確認する
				oldstatus =outlist[str(list[i])]
				oldlist = oldstatus.split("\t")

				#値の数が満たない場合はエラー
				if len(oldlist) < 2:
					logger.error("cannot get last value " + str(list[i])  )
					print "cannot get last value"
					continue	

				#前回がACTの場合
				if oldlist[2] == '[ACT]':

					#ホスト名の取得
					hostname = gethostname(str(list[i]))	
					##### TRAP出力 #####
					print " =========" + hostname + " Server Chenged [ACT] -> [SBY] ! ========="
					logger.error("=========" + hostname + " Server Chenged [ACT] -> [SBY] ! =========" )

					TRAPMSG = TRAPCOMM + " ========="+ hostname + " Server Chenged [ACT] -> [SBY] ! =========\""
					
					p=subprocess.Popen(TRAPMSG,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
					outMsg,errMsg = p.communicate()	
                                        if errMsg != "":
						logger.error("snmptrap send error " + str(list[i]) + " " + errMsg)
						print str(list[i]) + " snmptrap error " + errMsg
	

			#バッファに出力
                       	#現在時間の取得
                       	nowtime=datetime.datetime.now()
                       	nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')
			writestring += nowstr + "\t" + str(list[i]) + "\t" + '[SBY]\n'
				

	#ファイルに出力
	writeFile( writestring )

	time.sleep(SLEEP_TIME)
	

#!/usr/bin/env python
# coding:utf-8
import sys
import subprocess
import datetime
import time
import os
import logging
import logging.handlers

#分単位
ALERT_TERM=59

#status -1:障害 0:正常 9:トラップストップ 
OUTFNAME="SWING_PERFLOGCHECK"

SYSSWITCH_COMM ="/home/swing/sysswitchctl"
PERF_LOG_PATH="/usr/local/SWing/log/swing_perf.log"

LOGFILE="/root/swing_perfLogWatch.log"

NAME='%s' % os.uname()[1]
COMM="/usr/bin/snmptrap -v 1 -c public 192.168.41.214 1.3.6.1.4.1.9999 localhost 6 1 \'\' 1.3.6.1.4.1.9999.1 s \"" + NAME + " " + PERF_LOG_PATH

#ログローテーションの設定
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formater=logging.Formatter('%(asctime)s %(levelname)s %(message)s')
rfh=logging.handlers.RotatingFileHandler(
	filename=LOGFILE,
	maxBytes=10000000,
	backupCount=4
)
rfh.setLevel(logging.DEBUG)
rfh.setFormatter(formater)

logger.addHandler(rfh)

#系の状態取得
def getCluster():
	out= subprocess.Popen(SYSSWITCH_COMM, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
	outResult,errMsg = out.communicate()
	#判定を行う
	if outResult is None or outResult == "":
		print "Can Not Get Cluster Status "+ str(list[i]) + errMsg
		logger.error("Can Not Get Cluster Status "+  errMsg)
		return ""

	return outResult
		
#ファイル読み込み
def readfile():
	status=""
	alerttime=""
	
	#ファイルが存在しなかったら
	if os.path.exists(OUTFNAME) == False: 
		return status,alerttime
		
	for line in open(OUTFNAME,'r'):
	
		if line != "":
			try:
				status, alerttime = line[:-1].split('\t')
			except ValueError:
				print OUTFNAME + " CSV Illegal Data Format:" + __file__
				logger.error( OUTFNAME + " CSV Illegal Data Format")

	return status,alerttime

#ファイル書き込み
def writefile(str):

	#ファイルオープン
	f = open(OUTFNAME,'w')
	f.write(str)
	f.close()
	
#開始

outResult = getCluster()
#ACTかどうか
if '[ACT]' in outResult:

	#指定のログファイルの更新がされているかチェックを行う
	proc = subprocess.Popen('/usr/bin/find ' + PERF_LOG_PATH + ' -type f -mmin +30',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	out,err = proc.communicate()

	#正常に更新されていたらoutは空
	if out == "":

		#errに文字列が入っていたときはエラー
		if err != "":
			print __file__ + ": find Command Error! " + err
			logger.error( "find Command Error! " + err )
			#sys.exit(-1)

		#異常時からの復旧の場合復旧トラップ出力
		if os.path.exists(OUTFNAME):
			status,alerttime = readfile()
		
			#正常時(何もせず終了)Standbyからの切り替え時も
			if status == "0" or status == "1" :
				print __file__ + ":In Operating !"
				logger.info( "In Operating !")

				#ファイルを書き変える
                                nowtime=datetime.datetime.now()
                                nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')

                                #正常は0
                                str = '0' + '\t' + nowstr

                                #ファイルに書き込む
                                ret = writefile(str)	

			#前回エラー時
			elif status == "-1":

				print __file__ + ": Alert Recover  !! "
				logger.info( " Alert Recover  !! ")

				#フラグファイルが既に存在したら復旧アラーム出力
				COMMMSG = COMM + "--------- RECOVER Swing_perf.log update start !---------\""
			
				subprocess.call(COMMMSG,shell=True)

				nowtime=datetime.datetime.now()
				nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')
			
				#正常は0
				str = '0' + '\t' + nowstr
			
				#ファイルに書き込む
				ret = writefile(str)

			#メンテナンス時
			elif status == "9":
				print __file__ + ": Under a Mentenance."
				logger.warning( "Under a Mentenance.")

			#ファイル形式エラー
			else:
				logger.error( OUTFNAME + " File Format Error !!")
				print OUTFNAME + " File Format Error !!"
				#sys.exit(-1)
			
			#sys.exit()
		else:
			print __file__ + ":In Operating !"
			logger.info( "In Operating !")

			#ファイルを書き変える
			nowtime=datetime.datetime.now()
			nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')

			#正常は0
			str = '0' + '\t' + nowstr

			#ファイルに書き込む
			ret = writefile(str)
			
	else:
		#ファイルを読込
		status,alerttime = readfile()

		#パラメータを取得
		#フラグファイルの値取得エラー時
		if status is None or status == "" :

			print __file__ + ":perf.log First Alert Trap !!"
			logger.error( "First Alert Trap !! ")

			#フラグファイルが空の時は無条件にトラップ出力
			COMMMSG = COMM + " =========FIRST TIME Swing_perf.log Update Stopped !=========\""
			subprocess.call(COMMMSG,shell=True)

			#現在時間の取得
			nowtime=datetime.datetime.now()
			nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')

			#異常でフラグファイルに書き込む
			str = '-1\t' + nowstr

			#フラグファイルに書き込む
			writefile(str)

		#初回エラー時 Standby時
		elif status == "0" or status == "1":

			print __file__ + ": perf.log First Alert Trap !!"
			logger.error( "First Alert Trap !! ")

			#フラグファイルが空の時は無条件にトラップ出力
			COMMMSG = COMM + " =========FIRST TIME Swing_perf.log Update Stopped !=========\""
			subprocess.call(COMMMSG,shell=True)

			#現在時間の取得
			nowtime=datetime.datetime.now()
			nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')

			#異常でフラグファイルに書き込む
			str = '-1\t' + nowstr

			#フラグファイルに書き込む
			writefile(str)

		#前回エラー時
		#ステータス -1は停止状態
		elif status == "-1":

			#現在時間の取得
			nowtime=datetime.datetime.now()

			#現在時間から1時間引いた時間を取得
			now_old_time = nowtime - datetime.timedelta(minutes=ALERT_TERM)

			#アラート時間の取得
			#alerttimeob=datetime.datetime.strptime(alerttime,'%Y-%m-%d %H:%M:%S')
			alerttimeob=datetime.datetime(*time.strptime(alerttime,'%Y-%m-%d %H:%M:%S')[:-3])


			#アラート時間のほうが前であればアラートを表示する
			if now_old_time >= alerttimeob :

				print __file__ + ":REPEAT Alert Trap Return!! "
				logger.error( "REPEAT Alert Trap Return!! ")

				#トラップ出力
				COMMMSG = COMM + " =========REPEAT Swing_perf.log Update Stopped !=========\""
				subprocess.call(COMMMSG,shell=True)

				nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')
				str = '-1\t' + nowstr
				#フラグファイルに書き込む
				writefile(str)
			else:
				print __file__ + ":Alert but less than reguration time."
				logger.warning( "Alert but less than reguration time.")
		#トラップストップ
		elif status == "9":
			print __file__ + ":Under a Mentenance."
			logger.warning( "Under a Mentenance.")
		else:
			print OUTFNAME + " File Format Error !!:" + __file__
			logger.error( OUTFNAME + " File Format Error !!")
			#sys.exit(-1)
else:
	#ファイルを読込
	status,alerttime = readfile()
	if status == "9":
		print __file__ + ":Under a Mentenance."
		logger.warning( "Under a Mentenance.")	
	else:

		print __file__ + ":Standby Status."
		logger.info("Standby Status.")

       		nowtime=datetime.datetime.now()
		nowstr = nowtime.strftime('%Y-%m-%d %H:%M:%S')
		#待機系の場合は1を書込む
		str = '1\t' + nowstr
		#フラグファイルに書込む
		writefile(str)


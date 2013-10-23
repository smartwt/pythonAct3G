#!/bin/bash
`export LANG=ja_JP.utf8`
PROCESSLIST="/home/swing/psCheck/processlist"
PIDFILEPATH="/home/swing/psCheck/pidlog"
TMPFILE="/home/swing/psCheck/tmpdata"
i=0
lcnt=0
HAND=0
#パラメータがなかったら手動実行
if [ $# -ne 1 ]; then
	HAND=1
fi

#改行を区切文字としてファイルを1行づつ読込む
while IFS='\nEOT' read line
#cat $PROCESSLIST | while read line
do
	#タブを区切文字としてデータを取得
	IFS=$'\t'
	set -- $line
	#shortName=$1
	longName=$2
	shortName=`echo $1 | sed 's/ *$//g'`
	#longName=`echo $2 | sed 's/ *$//g'`

	#ロングネームが空なら何もしない
	if [ "$longName" = "" ]; then
		continue;
	fi
	#プロセスチェックを実行
	GYOU=`/bin/ps auxww | /bin/grep "${longName}" | /bin/grep -v /bin/grep | /usr/bin/wc -l`
	#行数を見て0行だった場合にエラー出力
	if [ $GYOU -ge 1 ]; then
	
		#起動プロセス数が1プロセスの時のみPIDをファイルに出力
		if [ $GYOU -eq 1 ]; then

			#PID取得
			PID=`/bin/ps auxww | /bin/grep "${longName}" | /bin/grep -v /bin/grep | awk '{ print $2 }' `
			c=0

			if [ ! -e $PIDFILEPATH ]; then
				`touch $PIDFILEPATH`
			fi

			#PIDファイルを開く
			flg=0
			while IFS='\n' read pidline
			do
				if [ ${#pidline} -ge 0 ]; then
					IFS=$'\t'
					set -- $pidline
					logpid=$1
					logshortName=$2
					loglongName=$3
					logcount=$4
					
					#プロセスロング名が合っているかチェック
					if [ ${longName} = ${loglongName} ]; then

						#PIDが同じかチェック
						if [ ${logpid} = ${PID} ]; then
							echo $PID "${shortName}------OK"
							flg=1
							break
						elif [ ${logpid} = -1 ]; then
							#プロセス名が合っているがpidが違う場合
							echo "########  ${shortName} プロセス数が変わりました。 ######## ORG:${logcount}  NEW:${GYOU}"
							flg=1
							`/bin/grep -v "${longName}" $PIDFILEPATH > $TMPFILE`
							`/bin/mv  $TMPFILE $PIDFILEPATH`
							echo $PID$'\t'${shortName}$'\t'${longName} >> $PIDFILEPATH

							#前回のチェックで2件以上起動していた場合はログ出力
							if [ $HAND != 1 ]; then
								`/usr/bin/logger -i ProcessCheck -p user.err "[ ${shortName} ] ########  The process count is changed!!  ######## ORG:${logcount}  NEW:1" `
							fi
						fi
					fi
					c=`expr $c + 1`
				fi
			done < $PIDFILEPATH

			#PIDlogにPIDがなかったときファイルに書き込む
			if [ $flg != 1 ];then

				echo "プロセスが新規に起動されましたプロセスID:[$PID] プロセス名:[$shortName]" 
				if [ ! -e $PIDFILEPATH ]; then								
					echo $PID$'\t'${shortName}$'\t'${longName} > $PIDFILEPATH
				else
					#ロング名が同じなのにPIDが違う場合
					`/bin/grep -v "${longName}" $PIDFILEPATH > $TMPFILE`
					`/bin/mv  $TMPFILE $PIDFILEPATH`
					echo $PID$'\t'${shortName}$'\t'${longName} >> $PIDFILEPATH
				fi
			fi
		else
		
			#============起動プロセスが1件以上の時、件数をチェックしpidlogファイルに出力============#
			c=0
			if [ ! -e $PIDFILEPATH ]; then
				`touch $PIDFILEPATH`
			fi
			flg=0
			while IFS='\nEOT' read pidline
			do

					IFS=$'\t'
					set -- $pidline
					logpid=$1
					logshortName=$2
					loglongName=$3
					logcount=$4

				if [ ${#pidline} -ge 0 ]; then
					if [ $logpid = -1 ]; then

						#存在チェック
						if [ ${loglongName} = ${longName} ]; then
						
							if [ ${GYOU} = ${logcount} ]; then
								#echo "${shortName} $GYOUプロセス起動中"
								flg=1
								break
							#行数とpidlogのプロセス数をチェック
							elif [ ${GYOU} != ${logcount} ]; then
								#logFileを書換え
								`/bin/grep -v "${loglongName}" $PIDFILEPATH > $TMPFILE`
								`/bin/mv  $TMPFILE $PIDFILEPATH`
								
								#プロセス数を変更
								echo "########  ${shortName} プロセス数が変わりました。 ######## ORG:${logcount}  NEW:${GYOU}"
								flg=1

								#プロセスがなかったときはファイルに書込む
								if [ ! -e $PIDFILEPATH ]; then
									echo "-1"$'\t'${shortName}$'\t'${longName}$'\t'${GYOU} > $PIDFILEPATH
								else
									echo "-1"$'\t'${shortName}$'\t'${longName}$'\t'${GYOU} >> $PIDFILEPATH
								fi

								#手動実行の時はログを飛ばさない
								if [ $HAND != 1 ]; then 
									`/usr/bin/logger -i ProcessCheck -p user.err "[ ${shortName} ] ########  The process count is changed!!  ######## ORG:${logcount}  NEW:${GYOU}" `
								fi
								break
							fi
						fi
					else
						#前回は1件の時
						logpid=$1
						logshortName=$2
						loglongName=$3
						logcount=$4
						#存在チェック
						if [ ${loglongName} = ${longName} ]; then
							#前回は1件で今回は複数ヒットした場合
							echo "########  ${shortName} プロセス数が変わりました。 ######## ORG:1  NEW:${GYOU}"
							flg=1

							#logFileを書換え
							`/bin/grep -v "${loglongName}" $PIDFILEPATH > $TMPFILE`
							`/bin/mv  $TMPFILE $PIDFILEPATH`

							#プロセスがなかったときはファイルに書込む
							if [ ! -e $PIDFILEPATH ]; then
								echo "-1"$'\t'${shortName}$'\t'${longName}$'\t'${GYOU} > $PIDFILEPATH
							else
								echo "-1"$'\t'${shortName}$'\t'${longName}$'\t'${GYOU} >> $PIDFILEPATH
							fi
							#手動実行の時はログを飛ばさない
							if [ $HAND != 1 ]; then 
								`/usr/bin/logger -i ProcessCheck -p user.err "[ ${shortName} ] ########  The process count is changed!!  ######## ORG:1  NEW:${GYOU}" `
							fi
							break

						fi
					fi
					c=`expr $c + 1`
				fi
			done < $PIDFILEPATH
			#プロセスがなかったときはファイルに書込む
			if [ $flg != 1 ];then
				echo "複数プロセス起動しました プロセス名:[$shortName]" 
				if [ ! -e $PIDFILEPATH ]; then
					echo "-1"$'\t'${shortName}$'\t'${longName}$'\t'${GYOU} > $PIDFILEPATH
				else
					echo "-1"$'\t'${shortName}$'\t'${longName}$'\t'${GYOU} >> $PIDFILEPATH
				fi
			fi
			
			#複数プロセス存在した場合は数だけ表示
			echo ${shortName}------$GYOU"件起動中"
		fi
		
		#STIME=`ls -ld --time-style=+'%Y/%m/%d %H:%M:%S' /proc/$PID | gawk '{print $6 " " $7}'`
		#DATE_1=`date -d $STIME '+%s'`
		#echo $DATE_1
				
		lcnt=`expr $lcnt + 1`
		
	##プロセスが存在しない場合
	else
    	echo "########  ERROR !! ${shortName} is NG !!  ########"
	    
	    #ログに出力 
		if [ $HAND != 1 ]; then 
	        `/usr/bin/logger -i ProcessCheck -p user.err "[ ${shortName} ] ########  ProcessError  ########" `
	    fi
    fi

	i=`expr $i + 1`
done < $PROCESSLIST

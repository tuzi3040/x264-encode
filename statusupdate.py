import logging
import json
import re
import time
import pymysql
import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkeci.request.v20180808.DescribeContainerLogRequest import DescribeContainerLogRequest

def handler(event, context):
	logger = logging.getLogger()
	
	eve = json.loads(event)
	akid = eve['akid']
	aksecret = eve['akse']
	regionid = 'cn-hangzhou'
	eciClient = AcsClient(akid,aksecret,regionid)
	
	taskid = eve['taskid']
	file = eve['file']
	cgid = eve['cgid']
	
	server = os.environ.get('server')
	database = os.environ.get('database')
	username = os.environ.get('username')
	password = os.environ.get('password')
	conn = pymysql.connect(host=server, user=username, password=password, db=database, charset='utf8mb4')
	cursor = conn.cursor()
	
	status = 'Container Group Created'
	progress = '0.0'
	cursor.execute("UPDATE `task` SET `Status` = \"" + status + "\", `Progress` = " + progress + " WHERE `Id` = \"" + taskid + "\"") 
	cursor.fetchone()
	conn.commit()
	
	request = DescribeContainerLogRequest()
	request.set_ContainerGroupId(cgid)
	request.set_ContainerName('encode')
	
	while True:
		response = eciClient.do_action_with_exception(request)
		responsej = json.loads(response)
		rescontent = responsej['Content']
		lenrescontent = len(rescontent)
		
		if lenrescontent <= 10:
			status = 'Container Created'
			cursor.execute("UPDATE `task` SET `Status` = \"" + status + "\" WHERE `Id` = \"" + taskid + "\"") 
			cursor.fetchone()
			conn.commit()
		elif lenrescontent <= 300:
			status = 'Initializing'
			cursor.execute("UPDATE `task` SET `Status` = \"" + status + "\" WHERE `Id` = \"" + taskid + "\"") 
			cursor.fetchone()
			conn.commit()
		else:
			status = 'Running'
			prop = re.compile(r'\[(?:[1-9]?[0-9]{1}|100)\.[0-9]{1}%\]')
			prod = prop.findall(rescontent)
			if prod:
				progress = prod[-1][1:-2]
			else:
				progress = '0.0'
			cursor.execute("UPDATE `task` SET `Status` = \"" + status + "\", `Progress` = " + progress + " WHERE `Id` = \"" + taskid + "\"") 
			cursor.fetchone()
			conn.commit()
			endind = re.search(rescontent, r'encoded \d+ frames')
			if endind:
				status = 'Complete'
				cursor.execute("UPDATE `task` SET `Status` = \"" + status + "\" WHERE `Id` = \"" + taskid + "\"") 
				cursor.fetchone()
				conn.commit()
				break
		time.sleep(3)
	cursor.close()
	conn.close()
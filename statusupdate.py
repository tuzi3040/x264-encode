import logging
import json
import re
import time
import pymssql
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
	conn = pymssql.connect(server=server, user=username, password=password, database=database)
	cursor = conn.cursor()
	
	status = 'Container Group Created'
	progress = 0.0
	cursor.execute("INSERT INTO [dbo].[task] ( [Id], [VideoFilename], [Status], [Progress] ) VALUES ( "+ taskid + ", " + file + ", " + status+ ", " + progress + " )") 
	cursor.fetchone()
	
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
			cursor.execute("UPDATE [dbo].[task] SET [Status] = " + status + " WHERE [Id] = " + taskid ) 
		elif lenrescontent <= 300:
			status = 'Initializing'
			cursor.execute("UPDATE [dbo].[task] SET [Status] = " + status + " WHERE [Id] = " + taskid ) 
		else:
			status = 'Running'
			prop = re.compile(r'^\[(?:[1-9]?[0-9]{1}|100)\.[0-9]{1}%\]')
			prod = prop.findall(rescontent)
			if prod:
				progress = float(prod[-1][1:-2])
			else:
				progress = 0.0
			cursor.execute("UPDATE [dbo].[task] SET [Status] = " + status + ", [Progress] = " + progress + " WHERE [Id] = " + taskid ) 
			endind = re.search(rescontent, r'^encoded \d+ frames')
			if endind:
				status = 'Complete'
				cursor.execute("UPDATE [dbo].[task] SET [Status] = " + status + " WHERE [Id] = " + taskid ) 
				cursor.fetchone()
				break
		cursor.fetchone()
		time.sleep(3)
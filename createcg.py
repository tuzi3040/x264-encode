import logging
import json
import base64
import fc2
import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkeci.request.v20180808.CreateContainerGroupRequest import CreateContainerGroupRequest

def handler(event, context):
	logger = logging.getLogger()
	#logger.info(str(logmes))
	
	eve = json.loads(event)

	file = eve['headers']['X-encode-file']
	taskid = eve['headers']['X-encode-id']
	
	#akid = context.credentials.access_key_id
	#aksecret = context.credentials.access_key_secret
	#aktoken = context.credentials.security_token
	akid = eve['headers']['X-akid']
	akse = eve['headers']['X-akse']
	regionid = 'cn-hangzhou'
	sgid = eve['headers']['X-encode-sgid']
	vsid = eve['headers']['X-encode-vsid']
	cgname = 'encode-' + taskid
	repouser = eve['headers']['X-encode-repouser']
	repopass = eve['headers']['X-encode-repopass']
	imagetag = eve['headers']['X-encode-imagetag']
	image = 'registry-vpc.cn-hangzhou.aliyuncs.com/tuzi3040/x264-encode:' + imagetag
	ossinput = 'oss://encode-e1/in/' + file + '_' + taskid + '.mp4'
	ossoutput = 'oss://encode-e1/out/' + file + '_' + taskid + '_out.mp4'
	osslog = 'oss://encode-e1/log/' + cgname + '.log'
	configc = '''#!/bin/bash
	ossutil cp -f ''' + ossinput + ''' /temp/t.mp4
	ffmpeg -i /temp/t.mp4 -vn -sn -c:a copy -y -map 0:a:0 /temp/t_atemp.aac
	x264 --crf 16.0 --preset 8 -I 600 -r 4 -b 3 --me umh -i 1 --scenecut 60 -f 1:1 --qcomp 0.5 --psy-rd 0.3:0 --aq-mode 2 --aq-strength 0.8 -o "/temp/t_vtemp.mp4" "/temp/t.mp4" 2>&1 | tee /temp/t.log
	MP4Box -add "/temp/t_vtemp.mp4#trackID=1:name=" -add "/temp/t_atemp.aac#trackID=1:name=" -new /temp/t_x264.mp4
	ossutil cp -f /temp/t_x264.mp4 ''' + ossoutput + '''
	ossutil cp -f /temp/t.log ''' + osslog
	configcontent = base64.b64encode(configc.encode('utf-8'))
	
	restartpolicy = 'OnFailure'
	eciClient = AcsClient(akid,akse,regionid)
	request = CreateContainerGroupRequest()
	request.set_SecurityGroupId(sgid)
	request.set_VSwitchId(vsid)
	request.set_ContainerGroupName(cgname)
	#request.set_EipInstanceId(eip-xxx)
	request.set_RestartPolicy(restartpolicy)
	
	config = {
		'Path': 'en',
		'Content': configcontent
	}
	
	volume1 = {
		'Name': 'temp',
		'Type': 'EmptyDirVolume'
	}
	volume2 = {
		'Name': 'scr',
		'Type': 'ConfigFileVolume',
	'ConfigFileVolume.ConfigFileToPaths': [config]
	}
	request.set_Volumes([volume1, volume2])
	
	volume_mount1 = {
		'Name': 'temp',
		'MountPath': '/temp',
		'ReadOnly': False
	}
	volume_mount2 = {
		'Name': 'scr',
		'MountPath': '/scr',
		'ReadOnly': False
	}
	
	container1 = {
		'Image': image,
		'Name': 'encode',
		'Cpu': 4.0,
		'Memory': 16.0,
		'ImagePullPolicy': 'Always',
		'Commands':['/bin/bash'],
		'Args': ['/scr/en'],
		'VolumeMounts':[volume_mount1,volume_mount2]
	}
	
	imagecre = {
		'Server': 'registry-vpc.cn-hangzhou.aliyuncs.com',
		'UserName': repouser,
		'Password': repopass
	}
	
	request.set_ImageRegistryCredentials([imagecre])
	request.set_Containers([container1])
	response = eciClient.do_action_with_exception(request)
	logger.info(response)
	
	respj = json.loads(response)
	cgid = respj['ContainerGroupId']
	
	fcakid = context.credentials.access_key_id
	fcakse = context.credentials.access_key_secret
	setoken = context.credentials.security_token
	fcclient = fc2.Client(
		endpoint=os.environ.get('fcep'),
		accessKeyID=fcakid,
		accessKeySecret=fcakse,
		securityToken=setoken
	)
	
	payload = {
		'akid': akid,
		'akse': akse,
		'taskid': taskid,
		'file': file,
		'cgid': cgid
	}
	fcpl = json.dumps(payload).encode('utf-8')
	fcclient.invoke_function('API-Encode', 'statusupdate', payload = fcpl, headers = {'x-fc-invocation-type': 'Async'})
	
	resp = {
		'isBase64Encoded': 'false',
		'statusCode': '200',
		'headers': {
			'X-encode-create': 'success'
		}
	}
	return json.dumps(resp)
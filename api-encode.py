import logging
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkeci.request.v20180808.CreateContainerGroupRequest import CreateContainerGroupRequest


def handler(event, context):
	logger = logging.getLogger()
	eve = json.loads(event)

	file = eve['headers']['X-encode-file']
	taskid = eve['headers']['X-encode-id']
	
	akid = context.credentials.access_key_id
	aksecret = context.credentials.access_key_secret
	#aktoken = context.credentials.security_token
	regionid = 'cn-hangzhou'
	sgid = eve['headers']['X-encode-sgid']
	vsid = eve['headers']['X-encode-vsid']
	cgname = 'encode-' + taskid
	repouser = eve['headers']['X-encode-repouser']
	repopass = eve['headers']['X-encode-repopass']
	imagetag = eve['headers']['X-encode-imagetag']
	image = 'registry-vpc.cn-hangzhou.aliyuncs.com/tuzi3040/x264-encode:' + imagetag
	ossinput = 'oss://encode-e1/in/' + file + '.mp4'
	ossoutput = 'oss://encode-e1/out/' + file + '_out.mp4'
	osslog = 'oss://encode-e1/log/' + cgname + '.log'
	configcontent = '''#!/bin/bash
	ossutil cp ''' + ossinput + ''' /temp/t.mp4
	x264 --crf 16.0 --preset 8	-I 600 -r 4 -b 3 --me umh -i 1 --scenecut 60 -f 1:1 --qcomp 0.5 --psy-rd 0.3:0 --aq-mode 2 --aq-strength 0.8 -o "/temp/t_vtemp.mp4" "/temp/t.mp4" 2>&1 | tee /temp/t.log
	ossutil cp /temp/t_vtemp.mp4 ''' + ossoutput + '''
	ossutil cp /temp/t.log ''' + osslog
	
	restartpolicy = 'OnFailure'
	eciClient = AcsClient(akid,aksecret,regionid)
	request = CreateCreateContainerGroupRequest()
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
	print response
	
	resp = {
		'isBase64Encoded': 'false',
		'statusCode': '200',
		'headers': {
			'X-encode-create': 'success'
		}
		
	}
	return json.dumps(resp)

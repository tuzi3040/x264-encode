from aliyunsdkcore.client import AcsClient
from aliyunsdkeci.request.v20180808.CreateContainerGroupRequest import CreateContainerGroupRequest


akid = ''
aksecret = ''
regionid = 'cn-hangzhou'
sgid = ''
vsid = ''
cgname = ''
restartpolicy = 'OnFailure'
eciClient = AcsClient(akid,aksecret,regionid)
request = CreateCreateContainerGroupRequest()
request.set_SecurityGroupId(sgid)
request.set_VSwitchId(vsid)
request.set_ContainerGroupName(cgname)
#request.set_EipInstanceId(eip-xxx)
request.set_RestartPolicy(restartpolicy)

volume1 = {
	'Name':'temp',
	'Type':'EmptyDirVolume',
	'EmptyDirVolume':True
}
volume2 = {
	'Name':'scr',
	'Type':'ConfigFileVolume',
	'ConfigFileVolume.ConfigFileToPaths':['en']
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

initContainer = {
	'Image': 'registry-vpc.cn-hangzhou.aliyuncs.com/baz/busybox:1.0',
	'Name': 'init-liu',
	'Cpu': 4.0,
	'Memory': 16.0,
	'VolumeMounts': [volume_mount1, volume_mount2],
	'Commands':['/bin/bash'],
	'Args': ['/scr/en'],
	'EnvironmentVars': [env]
}
container1 = {
	'Image': 'registry-vpc.cn-hangzhou.aliyuncs.com/tuzi3040/x264-encode:alpha-01',
	'Name': 'encode',
	'Cpu': 4.0,
	'Memory': 16.0,
	'ImagePullPolicy': 'Always',
	'Commands':['/bin/bash'],
	'Args': ['/scr/en'],
	'VolumeMounts':[volume_mount1,volume_mount2]
}

request.set_InitContainers([initContainer])
request.set_Containers([container1])
response = eciClient.do_action_with_exception(request)
print response

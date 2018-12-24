import logging
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkeci.request.v20180808.DeleteContainerGroupRequest import DeleteContainerGroupRequest
from aliyunsdkeci.request.v20180808.DescribeContainerGroupsRequest import DescribeContainerGroupsRequest

def handler(event, context):
	logger = logging.getLogger()
	
	eve = json.loads(event)
	akid = eve['headers']['X-akid']
	aksecret = eve['headers']['X-akse']
	regionid = 'cn-hangzhou'
	eciClient = AcsClient(akid,aksecret,regionid)

	taskid = eve['headers']['X-encode-id']

	descg = DescribeContainerGroupsRequest()
	cgname = 'encode-' + taskid
	descg.set_ContainerGroupName(cgname)
	cgs = eciClient.do_action_with_exception(descg)
	cgsj = json.loads(cgs)
	
	if not cgsj['ContainerGroups']:
		resp404 = {
			'isBase64Encoded': 'false',
			'statusCode': '404',
			'headers': {
				'X-encode-stopped': 'failed',
				'X-encode-failed': 'not found'
			}
		}
		return json.dumps(resp404)
		
	cgid = cgsj['ContainerGroups'][0]['ContainerGroupId']
	


	request = DeleteContainerGroupRequest()
	request.set_ContainerGroupId(cgid)
	response = eciClient.do_action_with_exception(request)
	
	logger.info(response)
	
	resp = {
		'isBase64Encoded': 'false',
		'statusCode': '200',
		'headers': {
			'X-encode-stopped': 'success'
		}
	}
	return json.dumps(resp)
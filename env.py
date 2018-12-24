import os
import subprocess as sp

def init(context):
	path = os.environ.get('FC_FUNC_CODE_PATH')
	p1 = sp.Popen("dpkg -i " + path + "/*.deb" , shell = True )
	p1.communicate()
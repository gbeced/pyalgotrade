# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from optparse import OptionParser
import sys
import subprocess


def parse_cmdline():
	usage = "usage: %prog [options]"
	parser = OptionParser(usage=usage)
	parser.add_option("-a", "--app_path", dest="app_path", help="Directory where app.yaml resides")
	mandatory_options = [
		"app_path"
			]

	(options, args) = parser.parse_args()

	# Check that all mandatory options are available.
	for opt in mandatory_options:
		if getattr(options, opt) == None:
			raise Exception("--%s option is missing" % opt)

	return (options, args)

class AppCfg:
	def __init__(self, appPath):
		self.__appPath = appPath

	def updateApp(self):
		cmd = []
		cmd.append("appcfg.py")
		cmd.append("update")
		cmd.append(self.__appPath)

		popenObj = subprocess.Popen(args=cmd)
		popenObj.communicate()

def main():
	try:
		(options, args) = parse_cmdline()
		appCfg = AppCfg(options.app_path)
		print "Updating application"
		appCfg.updateApp()
	except Exception, e:
		sys.stdout.write("Error: %s\n" % e)
		sys.exit(1)

if __name__ == "__main__":
	main()


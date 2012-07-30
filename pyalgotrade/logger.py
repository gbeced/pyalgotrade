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

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import logging

# Defaults
log_format = "%(asctime)s [%(levelname)s] %(message)s"
level=logging.INFO
file_log = None # File name
console_log = True

def __set_defaults(handler):
	handler.setFormatter(logging.Formatter(log_format))
	handler.setLevel(level)

def getLogger(name):
	ret = logging.getLogger(name)
	ret.setLevel(level)

	if file_log != None:
		fileHandler = logging.FileHandler(file_log)
		__set_defaults(fileHandler)
		ret.addHandler(fileHandler)

	if console_log:
		consoleHandler = logging.StreamHandler()
		__set_defaults(consoleHandler)
		ret.addHandler(consoleHandler)

	return ret


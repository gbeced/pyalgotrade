# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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

import threading
import copy

class Event:
	def __init__(self):
		self.__handlers = set()
		self.__lock = threading.Lock()

	def subscribe(self, handler):
		with self.__lock:
			self.__handlers.add(handler)

	def unsubscribe(self, handler):
		with self.__lock:
			self.__handlers.remove(handler)

	def emit(self, *parameters):
		with self.__lock:
			handlers = copy.copy(self.__handlers)

		for handler in handlers:
			handler(*parameters)


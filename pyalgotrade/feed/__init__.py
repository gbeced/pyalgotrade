# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import observer
from pyalgotrade import dataseries

class Feed(observer.Subject):
	def __init__(self, maxLen=dataseries.DEFAULT_MAX_LEN):
		assert(maxLen == None or maxLen > 0)
		self.__ds = {}
		self.__event = observer.Event()
		self.__maxLen = maxLen

	# Return True if this is a real-time feed.
	def isRealTime(self):
		raise NotImplementedError()

	# Subclasses should implement this and return the appropriate dataseries for the given key.
	def createDataSeries(self, key, maxLen):
		raise NotImplementedError()

	# Subclasses should implement this and return a (datetime.datetime, dict-like) tuple.
	def getNextValues(self):
		raise NotImplementedError()

	def registerDataSeries(self, key):
		if key not in self.__ds:
			self.__ds[key] = self.createDataSeries(key, self.__maxLen)

	def __getNextValuesAndUpdateDS(self):
		dateTime, values = self.getNextValues()
		if dateTime != None:
			# TODO: Check that dateTime is a datetime.datetime instance.
			for key, value in values.items():
				# Get or create the datseries for each key.
				try:
					ds = self.__ds[key]
				except KeyError:
					ds = self.createDataSeries(key, self.__maxLen)
					self.__ds[key] = ds
				ds.appendWithDateTime(dateTime, value)
		return values

	def __iter__(self):
		return self

	def next(self):
		if self.eof():
			raise StopIteration()
		return self.__getNextValuesAndUpdateDS()

	def getEvent(self):
		return self.__event

	def dispatch(self):
		values = self.__getNextValuesAndUpdateDS()
		if values != None:
			self.__event.emit(values)

	def getKeys(self):
		return self.__ds.keys()

	def __getitem__(self, key):
		"""Returns the :class:`pyalgotrade.dataseries.DataSeries` for a given instrument."""
		return self.__ds[key]

	def __contains__(self, key):
		"""Returns True if a :class:`pyalgotrade.dataseries.DataSeries` for the given instrument is available."""
		return key in self.__ds


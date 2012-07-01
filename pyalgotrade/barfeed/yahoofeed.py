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

from pyalgotrade.barfeed import csvfeed

import datetime

######################################################################
## Yahoo Finance CSV parser
# Each bar must be on its own line and fields must be separated by comma (,).
#
# Bars Format:
# Date,Open,High,Low,Close,Volume,Adj Close
#
# The csv Date column must have the following format: YYYY-MM-DD

class RowParser(csvfeed.YahooRowParser):
	pass

class Feed(csvfeed.YahooFeed):
	"""A :class:`pyalgotrade.barfeed.BarFeed` that loads bars from a CSV file downloaded from Yahoo! Finance."""
	def __init__(self):
		csvfeed.YahooFeed.__init__(self, True)
	
	def addBarsFromCSV(self, instrument, path, timeZone = 0):
		"""Loads bars for a given instrument from a CSV formatted file.
		The instrument gets registered in the bar feed.
		
		:param instrument: Instrument identifier.
		:type instrument: string.
		:param path: The path to the file.
		:type path: string.
		:param timeZone: The timezone for bars. 0 if bar dates are in UTC.
		:type timeZone: int.
		"""
		csvfeed.YahooFeed.addBarsFromCSV(self, instrument, path, timeZone)


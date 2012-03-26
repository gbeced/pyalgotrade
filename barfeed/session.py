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

class SessionCloseStrategy:
	# Return True if this is the last bar for the session. nextBar may be None.
	def sessionClose(self, currentBar, nextBar):
		raise Exception("Not implemented")

# Calculates session closes based on days. When the current bar is the last bar for the day, or the last bar in the feed, the session is closed.
class DaySessionCloseStrategy:
	def sessionClose(self, currentBar, nextBar):
		ret = False
		if nextBar == None:
			ret = True
		elif currentBar.getDateTime().date() != nextBar.getDateTime().date():
			ret = True
		return ret



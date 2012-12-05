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

# Calculates session close based on days.
# When the current bar is the last bar for the day, or the last bar in the feed, the session is closed.
def session_close(currentBar, nextBar):
	ret = False
	if nextBar == None:
		ret = True
	elif currentBar.getDateTime().date() != nextBar.getDateTime().date():
		ret = True
	return ret

# Sets session close and bars till session close properties to bars in a sequence. 
def set_session_close_attributes(barSeq, sessionCloseStrategy = None):
	for i in xrange(1, len(barSeq)):
		if session_close(barSeq[i-1], barSeq[i]):
			barSeq[i-1].setSessionClose(True)
			# Flag the penultimate bar if:
			# - There is a penultimate bar
			# - The penultimate and last bar belong to the same session.
			if i-2 >= 0 and session_close(barSeq[i-2], barSeq[i-1]) == False:
				barSeq[i-2].setBarsTillSessionClose(1)

	# Deal with the last bars in the feed.
	if len(barSeq):
		barSeq[-1].setSessionClose(True)
		if len(barSeq) > 1:
			barSeq[-2].setBarsTillSessionClose(1)


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

from pyalgotrade import execcontext
import math

def py_mean(values):
	ret = None
	if len(values):
		accum = 0
		for value in values:
			if value is None:
				return None
			accum += value
		ret = accum / float(len(values))
	return ret

def py_stddev(values, ddof = 1):
	ret = None
	if len(values):
		mn = mean(values)
		accum = 0
		for value in values:
			if value is None:
				return None
			accum += (value - mn)**2

		denom = len(values) - ddof
		if denom <= 0:
			return float('nan')
		ret = math.sqrt(accum / float(denom))
	return ret

if execcontext.running_in_google_app_engine:
	mean = py_mean
	stddev = py_stddev
else:
	import numpy

	def mean(values):
		ret = None
		if len(values):
			ret =  numpy.array(values).mean()
		return ret

	def stddev(values, ddof = 1):
		ret = None
		if len(values):
			ret =  numpy.array(values).std(ddof=ddof)
		return ret


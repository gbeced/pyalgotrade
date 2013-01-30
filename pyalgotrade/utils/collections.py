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

def lt(v1, v2):
	if v1 == None:
		return True
	elif v2 == None:
		return False
	else:
		return v1 < v2

# Returns (values, ix1, ix2)
# values1 and values2 are assumed to be sorted
def intersect(values1, values2, skipNone = False):
	ix1 = []
	ix2 = []
	values = []

	i1 = 0
	i2 = 0
	while i1 < len(values1) and i2 < len(values2):
		v1 = values1[i1]
		v2 = values2[i2]
		if v1 == v2 and (v1 != None or skipNone == False):
			ix1.append(i1)
			ix2.append(i2)
			values.append(v1)
			i1 += 1
			i2 += 1
		elif lt(v1, v2):
			i1 += 1
		else:
			i2 += 1

	return (values, ix1, ix2)


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

# Returns (values, ix1, ix2)
def intersect(seq1, seq2):
	# TODO: This is probably the lamest implementation. Optimize this.
	ix1 = []
	ix2 = []

	indDict1 = dict((k,i) for i,k in enumerate(seq1))
	indDict2 = dict((k,i) for i,k in enumerate(seq2))
	values = [x for x in set( indDict1.keys() ).intersection(indDict2.keys())]
	ix1 = [ indDict1[x] for x in values ]
	ix2 = [ indDict2[x] for x in values ]

	return (values, ix1, ix2)


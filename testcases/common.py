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

import csv
import os

from pyalgotrade import dataseries

def load_test_csv(path):
	inputSeq = []
	expectedSeq = []
	csvFile = open(path, "r")
	reader = csv.DictReader(csvFile)
	for row in reader:
		inputSeq.append(float(row["Input"]))
		expected = row["Expected"]
		if not expected:
			expected = None
		else:
			expected = float(expected)
		expectedSeq.append(expected)

	return (dataseries.SequenceDataSeries(inputSeq), dataseries.SequenceDataSeries(expectedSeq))

def normalize_value(value, decimals):
	if value != None:
		value = round(value, decimals)
	return value

def get_data_file_path(fileName):
	return os.path.join(os.path.split(__file__)[0], "data", fileName)

def test_from_csv(testcase, filename, filterClassBuilder, roundDecimals = 2, reverseOrder = False):
	inputDS, expectedDS = load_test_csv(get_data_file_path(filename))

	if reverseOrder:
		generator = xrange(inputDS.getLength()-1, -1, -1)
	else:
		generator = xrange(inputDS.getLength())

	filterInstance = filterClassBuilder(inputDS)
	for i in generator:
		value = normalize_value(filterInstance[i], roundDecimals)
		expectedValue = normalize_value(expectedDS[i], roundDecimals)
		testcase.assertEquals(value, expectedValue)


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
import shutil

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

	return inputSeq, expectedSeq

def normalize_value(value, decimals):
	if value != None:
		value = round(value, decimals)
	return value

def get_data_file_path(fileName):
	return os.path.join(os.path.split(__file__)[0], "data", fileName)

def test_from_csv(testcase, filename, filterClassBuilder, roundDecimals = 2, maxLen=dataseries.DEFAULT_MAX_LEN):
	inputValues, expectedValues = load_test_csv(get_data_file_path(filename))
	inputDS = dataseries.SequenceDataSeries(maxLen=maxLen)
	filterDS = filterClassBuilder(inputDS)
	for i in xrange(len(inputValues)):
		inputDS.append(inputValues[i])
		value = normalize_value(filterDS[i], roundDecimals)
		expectedValue = normalize_value(expectedValues[i], roundDecimals)
		testcase.assertEquals(value, expectedValue)

def init_temp_path():
	storage = get_temp_path()
	if not os.path.exists(storage):
		os.mkdir(storage)

def get_temp_path():
	return "data"

class CopyFiles:
	def __init__(self, files, dst):
		self.__files = files
		self.__dst = dst

	def __enter__(self):
		for src in self.__files:
			shutil.copy2(src, self.__dst)

	def __exit__(self, exc_type, exc_val, exc_tb):
		for src in self.__files:
			os.remove(os.path.join(self.__dst, os.path.basename(src)))


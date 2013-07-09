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

from pyalgotrade.utils import dt

def timestamp_to_tid(unixTime):
	return unixTime * 1000000

def tid_to_datetime(tid):
	unixTime = int(tid) / 1000000.0
	return dt.timestamp_to_datetime(unixTime)

def datetime_to_tid(dateTime):
	unixTime = dt.datetime_to_timestamp(dt.as_utc(dateTime))
	return timestamp_to_tid(unixTime)

# https://en.bitcoin.it/wiki/MtGox/API#Number_Formats
def from_value_int(currency, value_int):
	ret = int(value_int)
	if currency in ["JPY", "SEK"]:
		ret = ret * 0.001
	elif currency == "BTC":
		ret = ret * 0.00000001
	else:
		ret = ret * 0.00001
	return ret

def to_value_int(currency, value):
	if currency in ["JPY", "SEK"]:
		ret = value / 0.001
	elif currency == "BTC":
		ret = value / 0.00000001
	else:
		ret = value / 0.00001
	return ret

def to_amount_int(value):
	return value / 0.00000001

def from_amount_int(value_int):
	return int(value_int) * 0.00000001


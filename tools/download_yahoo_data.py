#!/usr/bin/env python

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

import argparse
import urllib
import sys

def __adjust_month(month):
	if month > 12 or month < 1:
		raise Exception("Invalid month")
	month -= 1 # Month for yahoo is 0 based
	return month

def __get_last_day(month):
	ret = 31
	if month in (4, 6, 9, 11):
		ret = 30
	elif month == 2:
		ret = 28
	return ret

def download_instrument_prices(instrument, fromMonth, fromYear, toMonth, toYear):
	fromDay = 1
	toDay = __get_last_day(toMonth)
	fromMonth = __adjust_month(fromMonth)
	toMonth = __adjust_month(toMonth)
	url = "http://ichart.finance.yahoo.com/table.csv?s=%s&a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&g=d&ignore=.csv" % (instrument, fromMonth, fromDay, fromYear, toMonth, toDay, toYear)

	f = urllib.urlopen(url)
	buff = f.read()

	# Remove the BOM
	while not buff[0].isalnum():
		buff = buff[1:]

	return buff

def main():
	parser = argparse.ArgumentParser(description='Download bars from Yahoo! Finance.')
	parser.add_argument('--month', required=False, type=int, nargs=1, help='The month to download. A number between 1 and 12. If it is not present, all months are downloaded.')
	parser.add_argument('--year', required=True, type=int, nargs=1, help='The year to download.')
	parser.add_argument('--instrument', required=True, type=str, nargs=1, help='The instrument to download.')
	args = parser.parse_args()

	instrument =  args.instrument[-1]
	year = args.year[-1]
	fromMonth = 1
	toMonth = 12
	if args.month:
		fromMonth = toMonth = args.month[-1]
	csv = download_instrument_prices(instrument, fromMonth, year, toMonth, year)
	print csv

if __name__ == "__main__":
	main()


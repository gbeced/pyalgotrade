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
.. module:: interactivebrokers
 :synopsis: Historical data downloader from Interactive Broker's TWS. 

.. moduleauthor:: Tibor Kiss <tibor.kiss@gmail.com>
"""
import csv

from pyalgotrade.providers.interactivebrokers import ibconnection


def __bars_to_csv(bars):
	"""Convert list of bars to list of CSV file rows
	Note: This function excludes the TWS Request ID from the data.
	"""
	# Convert Bar instances to Dict instances
	dicts = [{'Date':	bar.getDateTime(),
		  'Open':	bar.getOpen(),
		  'High':	bar.getHigh(),
		  'Low':	bar.getLow(),
		  'Close':	bar.getClose(),
		  'Volume':	bar.getVolume(),
		  'TradeCount': bar.getTradeCount(),
		  'VWAP':	bar.getVWAP(),
		 } for bar in bars]


	myCSV = []
	class _CSVDumper:
		@staticmethod
		def write(str):
			myCSV.append(str)

	dw = csv.DictWriter(_CSVDumper, 
			    ['Date','Open','High','Low','Close','Volume','TradeCount','VWAP'], 
			    extrasaction='ignore')
	dw.writeheader()
	dw.writerows(dicts)

	return myCSV

def get_historical_data(instrument, endTime, duration, barSize, 
			secType='STK', exchange='SMART', currency='USD', 
			whatToShow='TRADES', useRTH=0, formatDate=1, 
			twsHost='localhost', twsPort=7496, twsClientID=0): 
	"""Downloads historical data from IB through TWS.
	
	:param instrument: Ticker symbol
	:type instrument:  str
	:param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
	:type endTime:	str
	:param duration: This is the time span the request will cover, and is specified using the format: 
			 <integer> <unit>, i.e., 1 D, where valid units are:
			 S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
			 If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
	:type duration: str
	:param barSize: Specifies the size of the bars that will be returned (within IB/TWS limits). Valid values include:
			1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day
	:type barSize:	str
	:param whatToShow: Determines the nature of data being extracted. Valid values include:
			   TRADES, MIDPOINT, BID, ASK, BID_ASK, HISTORICAL_VOLATILITY, OPTION_IMPLIED_VOLATILITY
	:type whatToShow: str
	:param useRTH: Determines whether to return all data available during the requested time span, 
		       or only data that falls within regular trading hours. Valid values include:
		       0: All data is returned even where the market in question was outside of its regular trading hours.
		       1: Only data within the regular trading hours is returned, even if the requested time span
		       falls partially or completely outside of the RTH.
	:type useRTH: int
	:param formatDate: Determines the date format applied to returned bars. Valid values include:
			   1: Dates applying to bars returned in the format: yyyymmdd{space}{space}hh:mm:dd .
			   2: Dates are returned as a long integer specifying the number of seconds since 1/1/1970 GMT .
	:type formatDate: int
	:param twsHost: IP Address or Host where the TWS is running.
	:type twsHost: string
	:param twsPort: TCP Port where the TWS is listening.
	:type twsPort: int
	:param twsClientID: TWS Client ID. Must be unique for all connected clients.
	:type twsClientID: int
	"""

	connection = ibconnection.Connection('', 0, twsHost, twsPort, twsClientID)

	bars = connection.requestHistoricalData(instrument, endTime, duration, barSize,
						 secType, exchange, currency,
						 whatToShow, useRTH, formatDate)

	# Check for errors
	error = connection.getError()
	if error['tickerID'] != -1:
		print "ERROR: ", error

	# Return the loaded bars
	return bars


def get_1min_csv(instrument, endTime, duration): 
	"""Downloads historical data from IB using 1 minute bars

	:param instrument: Ticker symbol
	:type instrument: str
	:param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
	:type endTime:	str
	:param duration: This is the time span the request will cover, and is specified using the format: 
			 <integer> <unit>, i.e., 1 D, where valid units are:
			 S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
			 If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
	:type duration: str

	:rtype: List of the bars, where each list element is a CSV row.
	"""
	bars = get_historical_data(instrument, endTime, duration, barSize='1 min')
	return __bars_to_csv(bars)

def get_5min_csv(instrument, endTime, duration):
	"""Downloads historical data from IB using 5 minute bars

	:param instrument: Ticker symbol
	:type instrument: str
	:param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
	:type endTime:	str
	:param duration: This is the time span the request will cover, and is specified using the format: 
			 <integer> <unit>, i.e., 1 D, where valid units are:
			 S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
			 If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
	:type duration: str

	:rtype: List of the bars, where each list element is a CSV row.
	"""
	bars = get_historical_data(instrument, endTime, duration, barSize='5 mins')
	return __bars_to_csv(bars)

def get_daily_csv(instrument, endTime, duration): 
	"""Downloads historical data from IB using 1 day bars

	:param instrument: Ticker symbol
	:type instrument: str
	:param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
	:type endTime:	str
	:param duration: This is the time span the request will cover, and is specified using the format: 
			 <integer> <unit>, i.e., 1 D, where valid units are:
			 S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
			 If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
	:type duration: str

	:rtype: List of the bars, where each list element is a CSV row.
	"""
	bars = get_historical_data(instrument, endTime, duration, barSize='1 day')
	return __bars_to_csv(bars)


if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Historical data downloader from Interactive Broker\'s  TWS')
	parser.add_argument('--instrument',   help='Ticker symbol', required=True)
	parser.add_argument('--endtime',  help='Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.',
			    nargs='*', required=True,
			   )
	parser.add_argument('--duration', help='This is the time span the request will cover, and is specified using the format:\n'
					       '<integer> <unit>, i.e., 1 D, where valid units are:\n'
					       'S (seconds),  D (days),  W (weeks),  M (months),  Y (years)\n'
					       'If no unit is specified, seconds are used.',
			    default=['1', 'D'],
			    nargs=2,
			    )
	parser.add_argument('--barsize', help='Specifies the size of the bars that will be returned (within IB/TWS limits). Valid values include:\n'
					      '1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day',
			    default=['5', 'mins'],
			    nargs=2,
			    )

	args = parser.parse_args()

	bars = get_historical_data(args.instrument, " ".join(args.endtime), " ".join(args.duration), " ".join(args.barsize))
	csv_rows = __bars_to_csv(bars)

	for row in csv_rows:
		print row, 

# vim: noet:ci:pi:sts=0:sw=4:ts=4

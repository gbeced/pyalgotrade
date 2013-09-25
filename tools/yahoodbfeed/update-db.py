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

import sys
sys.path.append("../..")

import pyalgotrade.logger

pyalgotrade.logger.file_log = "update-db.log"
logger = pyalgotrade.logger.getLogger("update-db")

from pyalgotrade.barfeed import sqlitefeed
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade import marketsession
from pyalgotrade.tools import yahoofinance

import os

storage = "data"

def get_csv_filename(symbol, year):
	return os.path.join(storage, "%s-%d-yahoofinance.csv" % (symbol, year))

def download_files_for_symbol(symbol, fromYear, toYear):
	if not os.path.exists(storage):
		logger.info("Creating %s directory" % (storage))
		os.mkdir(storage)

	status = ""
	for year in range(fromYear, toYear+1):
		fileName = get_csv_filename(symbol, year)
		if not os.path.exists(fileName):
			logger.info("Downloading %s %d to %s" % (symbol, year, fileName))
			try: 
				yahoofinance.download_daily_bars(symbol, year, fileName)
				status += "1"
			except Exception, e:
				logger.error(str(e))
				status += "0"
		else:
			status += "1"

	if status.find("1") == -1:
		logger.fatal("No data found for %s" % (symbol))
	elif status.lstrip("0").find("0") != -1:
		logger.fatal("Some bars are missing for %s" % (symbol))

def download_files(symbolsFile, fromYear, toYear):
	for symbol in open(symbolsFile, "r"):
		symbol = symbol.strip()
		download_files_for_symbol(symbol, fromYear, toYear)

def update_db_for_symbol(db, symbol, timezone, fromYear, toYear):
	feed = yahoofeed.Feed(timezone)
	feed.sanitizeBars(True)
	for year in range(fromYear, toYear+1):
		fileName = get_csv_filename(symbol, year)
		if os.path.exists(fileName):
			feed.addBarsFromCSV(symbol, fileName, timezone)
	db.addBarsFromFeed(feed)

def update_db(dbFilePath, symbolsFile, timezone, fromYear, toYear):
	db = sqlitefeed.Database(dbFilePath)
	for symbol in open(symbolsFile, "r"):
		symbol = symbol.strip()
		logger.info("Updating %s bars" % (symbol))
		update_db_for_symbol(db, symbol, timezone, fromYear, toYear)

# Symbols
# http://www.nasdaq.com/screening/companies-by-name.aspx?exchange=NYSE&render=download
# http://www.nasdaq.com/screening/companies-by-name.aspx?exchange=NASDAQ&render=download

def main():
	fromYear = 2000
	toYear = 2012

	symbolsFile = "nyse-symbols.txt"
	dbFile = "nyse.sqlite"
	timezone = marketsession.USEquities.timezone

	# symbolsFile = "merval-symbols.txt"
	# dbFile = "merval.sqlite"
	# timezone = marketsession.MERVAL.timezone

	# download_files(symbolsFile, fromYear, toYear)
	# update_db(dbFile, symbolsFile, timezone, fromYear, toYear)

main()


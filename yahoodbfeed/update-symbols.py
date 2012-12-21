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

import urllib2
import BeautifulSoup

import sys
sys.path.append("..")

import pyalgotrade.logger

logger = pyalgotrade.logger.getLogger("update-symbols")

def get_symbols_filename(market):
	market = market.lower()
	return "%s-symbols.txt" % (market)

def get_symbols_from_page(url):
	#<tr class="ro" onclick="location.href='/stockquote/NASDAQ/AAC.htm';" style="color:green;">
	#	<td><A href="/stockquote/NASDAQ/AAC.htm" title="Display Quote &amp; Chart for NASDAQ,AAC">AAC</A></td>
	#	<td>Australia Acquisition</td>
	#	<td align=right>10.03</td>
	#	<td align=right>10.02</td>
	#	<td align=right>10.03</td>
	#	<td align=right>11,000</td>
	#	<td align="right">0.05</td>
	#	<td align="center"><IMG src="/images/up.gif"></td>
	#	<td align="left">0.50</td>
	#	<td align="right"><a href="/stockquote/NASDAQ/AAC.htm" title="Download Data for NASDAQ,AAC"><img src="/images/dl.gif" width=14 height=14></a>&nbsp;<a href="/stockquote/NASDAQ/AAC.htm" title="View Quote and Chart for NASDAQ,AAC"><img src="/images/chart.gif" width=14 height=14></a></td>
	#</tr>

	ret = []
	html = urllib2.urlopen(url).read()

	predicate = lambda tag: tag.name == "tr" and (("class", "ro") in tag.attrs or ("class", "re") in tag.attrs)
	soup = BeautifulSoup.BeautifulSoup(html)
	tags = soup.findAll(predicate)
	for tag in tags:
		ret.append(tag.contents[0].contents[0].contents[0].strip())
	return ret

def download_symbols(market):
	market = market.upper()
	pages = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
	for x in pages:
		url = "http://www.eoddata.com/stocklist/%s/%s.htm" % (market, x)
		logger.info("Processing %s" % url)
		for symbol in get_symbols_from_page(url):
			yield symbol

def build_symbols_file(market):
	symbolsFile = open(get_symbols_filename(market), "w")
	for symbol in download_symbols(market):
		symbolsFile.write("%s\n" % symbol)

def main():
	build_symbols_file("nasdaq")
	build_symbols_file("nyse")

main()


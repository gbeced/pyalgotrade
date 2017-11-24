# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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
import lxml.html
import symbolsxml

# pyalgotrade.logger.file_log = "get_sp500_symbols.log"
logger = pyalgotrade.logger.getLogger("get_sp500_symbols")

TICKER_SYMBOL_COL = 0
COMPANY_COL = 1
GICS_COL = 3
GICS_SUB_INDUSTRY_COL = 4


def get_html():
    logger.info("Getting S&P 500 Component Stocks from Wikipedia")
    ret = lxml.html.parse("http://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    return ret


def find_table(htmlTree):
    logger.info("Finding the right table")
    ret = None
    tables = htmlTree.xpath("//table[@class='wikitable sortable']")
    for table in tables:
        headers = table.xpath("tr[1]/th")
        if len(headers) > 5:
            if headers[TICKER_SYMBOL_COL].xpath("a[1]")[0].text != "Ticker symbol":
                continue
            if headers[COMPANY_COL].text != "Company":
                continue
            if headers[GICS_COL].xpath("a[1]")[0].text != "GICS":
                continue
            if headers[GICS_SUB_INDUSTRY_COL].text != "GICS Sub Industry":
                continue
            ret = table
            break
    return ret


def parse_results(table):
    ret = symbolsxml.Writer()
    logger.info("Parsing table")
    rows = table.xpath("tr")
    for row in rows[1:]:
        cols = row.xpath("td")
        tickerSymbol = cols[TICKER_SYMBOL_COL].xpath("a[1]")[0].text
        company = cols[COMPANY_COL].xpath("a[1]")[0].text
        gics = cols[GICS_COL].text
        gicsSubIndustry = cols[GICS_SUB_INDUSTRY_COL].text
        if gicsSubIndustry is None:
            gicsSubIndustry = ""

        ret.addStock(tickerSymbol, company, gics, gicsSubIndustry)
    return ret


def main():
    try:
        htmlTree = get_html()
        table = find_table(htmlTree)
        if table is None:
            raise Exception("S&P 500 Component Stocks table not found")
        symbolsXML = parse_results(table)

        logger.info("Writing sp500.xml")
        symbolsXML.write("sp500.xml")
    except Exception as e:
        logger.error(str(e))

if __name__ == "__main__":
    main()

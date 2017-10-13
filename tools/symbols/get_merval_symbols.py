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

logger = pyalgotrade.logger.getLogger("get_merval_symbols")


def find_company(htmlTree, ticker):
    ret = None
    anchor = htmlTree.xpath("//td[1]/a[@href='/q/pr?s=%s']/text()" % (ticker))
    if anchor:
        ret = anchor[0]
    return ret


def find_sector(htmlTree):
    ret = None
    anchor = htmlTree.xpath("//th[1][text() = 'Sector:']/../td/a[1]/text()")
    if anchor:
        ret = anchor[0]
    return ret


def find_industry(htmlTree):
    ret = None
    anchor = htmlTree.xpath("//th[1][text() = 'Industry:']/../td/a[1]/text()")
    if anchor:
        ret = anchor[0]
    return ret


def process_symbol(writer, symbol):
    try:
        logger.info("Getting info for %s" % (symbol))
        url = "http://finance.yahoo.com/q/in?s=%s+Industry" % (symbol)
        htmlTree = lxml.html.parse(url)

        company = find_company(htmlTree, symbol)
        if not company:
            raise Exception("Company name not found")

        sector = find_sector(htmlTree)
        if not sector:
            sector = ""
            logger.warning("Sector not found")

        industry = find_industry(htmlTree)
        if not industry:
            industry = ""
            logger.warning("Industry not found")

        writer.addStock(symbol, company, sector, industry)
    except Exception as e:
        logger.error(str(e))


def main():
    try:
        writer = symbolsxml.Writer()
        for symbol in open("merval-symbols.txt", "r"):
            symbol = symbol.strip()
            process_symbol(writer, symbol)

        # Index
        writer.addIndex("^MERV", "Merval")

        logger.info("Writing merval.xml")
        writer.write("merval.xml")
    except Exception as e:
        logger.error(str(e))

if __name__ == "__main__":
    main()

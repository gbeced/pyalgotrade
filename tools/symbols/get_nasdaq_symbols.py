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
import tempfile
import urllib.request, urllib.error, urllib.parse
import csv
import symbolsxml


logger = pyalgotrade.logger.getLogger("get_nasdaq_symbols")


def main():
    try:
        logger.info("Getting NASDAQ symbols from http://www.nasdaq.com/")
        url = "http://www.nasdaq.com/screening/companies-by-name.aspx?exchange=NASDAQ&render=download"
        buff = urllib.request.urlopen(url).read()

        tmpFile = tempfile.NamedTemporaryFile()
        tmpFile.write(buff)
        tmpFile.flush()
        with open(tmpFile.name, 'rb') as csvfile:
            symbolsXML = symbolsxml.Writer()
            for row in csv.DictReader(csvfile):
                symbolsXML.addStock(row["Symbol"], row["Name"], row["Sector"], row["industry"])

        logger.info("Writing nasdaq.xml")
        symbolsXML.write("nasdaq.xml")
    except Exception as e:
        logger.error(str(e))

if __name__ == "__main__":
    main()

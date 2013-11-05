# PyAlgoTrade
#
# Copyright 2011-2013 Gabriel Martin Becedillas Ruiz
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

from lxml import etree


class Writer:
    def __init__(self):
        self.__root = etree.Element('symbols')

    def add(self, ticker, company, sector, industry):
        symbolElement = etree.Element("symbol")
        symbolElement.set("ticker", ticker)
        symbolElement.set("company", company)
        if sector is None:
            sector = ""
        symbolElement.set("sector", sector)
        if industry is None:
            industry = ""
        symbolElement.set("industry", industry)
        self.__root.append(symbolElement)

    def write(self, fileName):
        etree.ElementTree(self.__root).write(fileName, xml_declaration=True, encoding="utf-8", pretty_print=True)

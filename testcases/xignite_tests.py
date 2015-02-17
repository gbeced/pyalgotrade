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

import datetime
import json

import common

from pyalgotrade.xignite import api
from pyalgotrade.xignite import barfeed
from pyalgotrade.utils import dt


class DateTimeTestCase(common.TestCase):
    def testMarketTimes(self):
        # 9:30 in GMT-5
        dateTime = dt.as_utc(datetime.datetime(2013, 1, 1, 9+5, 30))
        self.assertEqual(dt.unlocalize(api.to_market_datetime(dateTime, "XNYS")), datetime.datetime(2013, 1, 1, 9, 30))
        self.assertEqual(dt.unlocalize(api.to_market_datetime(dateTime, "XASE")), datetime.datetime(2013, 1, 1, 9, 30))
        self.assertEqual(dt.unlocalize(api.to_market_datetime(dateTime, "XNAS")), datetime.datetime(2013, 1, 1, 9, 30))
        self.assertEqual(dt.unlocalize(api.to_market_datetime(dateTime, "XNYS")), datetime.datetime(2013, 1, 1, 9, 30))

        # 8:00 in GMT
        dateTime = dt.as_utc(datetime.datetime(2013, 1, 1, 8))
        self.assertEqual(dt.unlocalize(api.to_market_datetime(dateTime, "CHIX")), datetime.datetime(2013, 1, 1, 8))
        # From Apr~Oct CHIX is GMT+1
        dateTime = dt.as_utc(datetime.datetime(2013, 4, 1, 8))
        self.assertEqual(dt.unlocalize(api.to_market_datetime(dateTime, "CHIX")), datetime.datetime(2013, 4, 1, 9))

    def testBuildBar(self):
        # This is the response to http://globalrealtime.xignite.com/v3/xGlobalRealTime.json/GetBar?Identifier=RIOl.CHIX&IdentifierType=Symbol&EndTime=3/19/2014%2010:00:00&Precision=Minutes&Period=5
        response = """{
            "Outcome": "Success",
            "Message": null,
            "Identity": "Request",
            "Delay": 0.0330687,
            "Bar": {
                "StartDate": "3/19/2014",
                "StartTime": "9:55:00 AM",
                "EndDate": "3/19/2014",
                "EndTime": "10:00:00 AM",
                "UTCOffset": 0,
                "Open": 31.71,
                "High": 31.71,
                "Low": 31.68,
                "Close": 31.69,
                "Volume": 2966,
                "Trades": 19,
                "TWAP": 31.6929,
                "VWAP": 31.693
            },
            "Security": {
                "CIK": "0000863064",
                "CUSIP": null,
                "Symbol": "RIOl.CHIX",
                "ISIN": null,
                "Valoren": "402589",
                "Name": "Rio Tinto PLC",
                "Market": "CHI-X EUROPE LIMITED.",
                "MarketIdentificationCode": "CHIX",
                "MostLiquidExchange": false,
                "CategoryOrIndustry": "IndustrialMetalsAndMinerals"
            }
        }"""

        responseDict = json.loads(response)
        bar = barfeed.build_bar(responseDict["Bar"], "RIOl.CHIX", 60*5)

        self.assertEqual(bar.getOpen(), 31.71)
        self.assertEqual(bar.getHigh(), 31.71)
        self.assertEqual(bar.getLow(), 31.68)
        self.assertEqual(bar.getClose(), 31.69)
        self.assertEqual(bar.getVolume(), 2966)
        self.assertEqual(bar.getDateTime(), dt.as_utc(datetime.datetime(2014, 3, 19, 9, 55)))

# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

import urlparse
import urllib
import urllib2
import json
# import pytz

from pyalgotrade.utils import dt
from pyalgotrade import marketsession

USE_SECURE_REQUESTS = False

# https://www.xignite.com/product/global-real-time-stock-quote-data/api/ListExchanges/
MARKET_TIMEZONES = {
        "ARCX": None,  # NYSE ARCA
        "CHIX": marketsession.NYSE.timezone,  # CHI-X EUROPE LIMITED
        "OOTC": None,  # OTHER OTC/NBB
        "PINX": None,  # OTC PINK MARKETPLACE
        "XASE": marketsession.NYSE.timezone,  # NYSE MKT EQUITIES
        "XNAS": marketsession.NASDAQ.timezone,  # NASDAQ
        "XNYS": marketsession.NYSE.timezone,  # NEW YORK STOCK EXCHANGE, INC
        "XOTC": None,  # OTC BULLETIN BOARD
        }


class XigniteError(Exception):
    def __init__(self, message, response):
        Exception.__init__(self, message)
        self.__response = response

    def getResponse(self):
        return self.__response


def to_market_datetime(dateTime, exchange):
    timezone = MARKET_TIMEZONES.get(exchange)
    if timezone is None:
        raise Exception("No timezone available to localize datetime for exchange %s" % (exchange))
    return dt.localize(dateTime, timezone)


def datetime_to_string(dateTime, exchange):
    # MM/DD/YYYY HH:MM
    return to_market_datetime(dateTime, exchange).strftime("%m/%d/%Y %H:%M")


def json_http_request(url):
    f = urllib2.urlopen(url)
    response = f.read()
    return json.loads(response)

def XigniteGlobalRealTime_GetBar(token, identifier, identifierType, exchange, endDateTime, precision, period, secureRequest=None):
    if dt.datetime_is_naive(endDateTime):
        raise Exception("endDateTime must have a timezone")

    if secureRequest is None:
        secureRequest = USE_SECURE_REQUESTS

    if secureRequest:
        scheme = "https"
    else:
        scheme = "http"

    # print datetime_to_string(endDateTime, exchange)
    params = {"_Token": token,
            "Identifier": "%s.%s" % (identifier, exchange),
            "IdentifierType": identifierType,
            "EndTime": datetime_to_string(endDateTime, exchange),
            "Precision": precision,
            "Period": period,
            }
    parts = (scheme, "globalrealtime.xignite.com", "v3/xGlobalRealTime.json/GetBar", urllib.urlencode(params), "")
    url = urlparse.urlunsplit(parts)

    ret = json_http_request(url)
    if ret.get("Outcome") != "Success":
        msg = ret.get("Message")
        if msg is None:
            msg = "Error %s" % (ret.get("Outcome"))
        raise XigniteError(msg, ret)

    return ret


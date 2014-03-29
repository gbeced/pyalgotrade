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
import pytz

from pyalgotrade.utils import dt


USE_SECURE_REQUESTS = False

# The exchange list comes from:
#  https://www.xignite.com/product/global-real-time-stock-quote-data/api/ListExchanges/
#
# I couldn't deduce the timezones for OOTC, PINX and XOTC using:
#  https://www.xignite.com/product/XigniteGlobalExchanges/api/GetExchangeHoursUTC/
#  https://www.xignite.com/product/XigniteGlobalExchanges/api/GetExchangeHours/

MARKET_TIMEZONES = {
    "ARCX": pytz.timezone("US/Eastern"),     # NYSE ARCA
    "CHIX": pytz.timezone("Europe/London"),  # CHI-X EUROPE LIMITED
    "XASE": pytz.timezone("US/Eastern"),     # NYSE MKT EQUITIES
    "XNAS": pytz.timezone("US/Eastern"),     # NASDAQ
    "XNYS": pytz.timezone("US/Eastern"),     # NEW YORK STOCK EXCHANGE, INC
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


def parse_instrument_exchange(identifier):
    ret = identifier.split(".")
    if len(ret) != 2:
        raise Exception("Invalid identifier. Exchange suffix is missing")
    return ret


# https://www.xignite.com/product/global-real-time-stock-quote-data/api/GetBar/
def XigniteGlobalRealTime_GetBar(token, identifier, identifierType, endDateTime, precision, period, secureRequest=None):
    if dt.datetime_is_naive(endDateTime):
        raise Exception("endDateTime must have a timezone")

    # Parse the exchange from the identifier.
    instrument, exchange = parse_instrument_exchange(identifier)

    if secureRequest is None:
        secureRequest = USE_SECURE_REQUESTS

    if secureRequest:
        scheme = "https"
    else:
        scheme = "http"

    # print datetime_to_string(endDateTime, exchange)
    params = {
        "_Token": token,
        "Identifier": identifier,
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

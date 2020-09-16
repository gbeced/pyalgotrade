# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import dispatcher
from pyalgotrade.bitstamp import barfeed


def test_bar_feed_with_multiple_instruments():
    instruments = ["BTC/USD", "BTC/EUR"]

    test_timeout = datetime.datetime.now() + datetime.timedelta(minutes=5)
    bar_events = set()
    order_book_updates = set()

    disp = dispatcher.Dispatcher()
    barFeed = barfeed.LiveTradeFeed(instruments)
    disp.addSubject(barFeed)

    def done_testing():
        # Did we receive updates for all instruments and all entities ?
        ret = bar_events ^ set(instruments) == set()
        ret = ret and order_book_updates ^ set(instruments) == set()
        return ret or datetime.datetime.now() > test_timeout

    def on_bars(dateTime, bars):
        for bar in bars:
            bar_events.add(bar.getInstrument())
        if done_testing():
            disp.stop()

    def on_order_book_updated(orderBookUpdate):
        order_book_updates.add(orderBookUpdate.getInstrument())
        if done_testing():
            disp.stop()

    def on_idle():
        if done_testing():
            disp.stop()

    # Subscribe to events.
    barFeed.getNewValuesEvent().subscribe(on_bars)
    barFeed.getOrderBookUpdateEvent().subscribe(on_order_book_updated)
    disp.getIdleEvent().subscribe(on_idle)
    disp.run()

    # Check that we received events for all instruments and all entities.
    assert bar_events ^ set(instruments) == set()
    assert order_book_updates ^ set(instruments) == set()

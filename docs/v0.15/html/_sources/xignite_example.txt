.. _xignite-tutorial-label:

Xignite Example
===============

This goal of this example is to show how to put all the pieces together to paper
trade a strategy using realtime feeds supplied by Xignite (https://www.xignite.com/).

This example assumes that you're already familiar with the basic concepts presented
in the :ref:`tutorial-label` section.

The key things to highlight are:

 1. We're using :class:`pyalgotrade.strategy.BaseStrategy` instead of :class:`pyalgotrade.strategy.BacktestingStrategy`
    as the base class. This is not a backtest.
 2. :class:`pyalgotrade.xignite.barfeed.LiveFeed` is used to pull 5 minute bars directly from Xignite. In order to use this service
    you need to sign up for the XigniteGlobalRealTime API (https://www.xignite.com/product/global-real-time-stock-quote-data/)
    to get an API token.
 3. As described in https://www.xignite.com/product/global-real-time-stock-quote-data/api/GetBar/, indentifiers are fully qualified
    identifiers for the security as determined by the **IdentifierType** parameter. You **must** include the exchange suffix.
 4. You can only paper trade while the market is open.
 5. The 5 minute bars are requested 60 seconds after the 5 minute window closes because data may not be immediately available.

.. literalinclude:: ../samples/tutorial_xignite_1.py

The output should look like this: ::

    2014-03-28 09:31:01,389 strategy [INFO] HSBAl.CHIX: Open: 6.093 High: 6.102 Low: 6.093 Close: 6.101 Volume: 45635.0 SMA: None
    2014-03-28 09:31:01,390 strategy [INFO] RIOl.CHIX: Open: 33.08 High: 33.08 Low: 33.065 Close: 33.07 Volume: 2303.0 SMA: None
    2014-03-28 09:36:01,494 strategy [INFO] HSBAl.CHIX: Open: 6.102 High: 6.102 Low: 6.099 Close: 6.099 Volume: 21043.0 SMA: None
    2014-03-28 09:36:01,495 strategy [INFO] RIOl.CHIX: Open: 33.075 High: 33.09 Low: 33.055 Close: 33.055 Volume: 2909.0 SMA: None
    2014-03-28 09:41:01,885 strategy [INFO] HSBAl.CHIX: Open: 6.101 High: 6.101 Low: 6.097 Close: 6.097 Volume: 29075.0 SMA: None
    2014-03-28 09:41:01,886 strategy [INFO] RIOl.CHIX: Open: 33.04 High: 33.04 Low: 33.005 Close: 33.005 Volume: 895.0 SMA: None
    2014-03-28 09:46:00,943 strategy [INFO] HSBAl.CHIX: Open: 6.098 High: 6.098 Low: 6.093 Close: 6.094 Volume: 17955.0 SMA: None
    2014-03-28 09:46:00,943 strategy [INFO] RIOl.CHIX: Open: 33.005 High: 33.035 Low: 32.995 Close: 32.995 Volume: 4052.0 SMA: None
    2014-03-28 09:51:01,604 strategy [INFO] HSBAl.CHIX: Open: 6.093 High: 6.099 Low: 6.092 Close: 6.097 Volume: 28046.0 SMA: 6.0976
    2014-03-28 09:51:01,604 strategy [INFO] RIOl.CHIX: Open: 32.99 High: 33.025 Low: 32.985 Close: 32.99 Volume: 2823.0 SMA: 33.023
    2014-03-28 09:56:01,511 strategy [INFO] HSBAl.CHIX: Open: 6.099 High: 6.1 Low: 6.096 Close: 6.098 Volume: 19713.0 SMA: 6.097
    2014-03-28 09:56:01,511 strategy [INFO] RIOl.CHIX: Open: 32.98 High: 33.01 Low: 32.96 Close: 33.01 Volume: 1545.0 SMA: 33.011
    .
    .
    .


When apiCallDelay is not long enough, or when there is no data at all, you may receive the following error message: ::

    xignite [ERROR] No ticks available for Symbol:RIOl.CHIX from 3/28/2014 1:10:00 PM to 3/28/2014 1:11:00 PM.


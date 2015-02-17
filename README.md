PyAlgoTrade
===========

[![version status](https://pypip.in/v/pyalgotrade/badge.png)](https://pypi.python.org/pypi/pyalgotrade)
[![downloads](https://pypip.in/d/pyalgotrade/badge.png)](https://pypi.python.org/pypi/pyalgotrade)
[![build status](https://travis-ci.org/gbeced/pyalgotrade.png?branch=master)](https://travis-ci.org/gbeced/pyalgotrade)

PyAlgoTrade is an **event driven algorithmic trading** Python library. Although the initial focus
was on **backtesting**, **paper trading** is now possible using:

 * [Bitstamp](https://www.bitstamp.net/) for Bitcoins
 * [Xignite](https://www.xignite.com/) for stocks

and **live trading** is now possible using:

 * [Bitstamp](https://www.bitstamp.net/) for Bitcoins

To get started with PyAlgoTrade take a look at the [tutorial](http://gbeced.github.io/pyalgotrade/docs/v0.16/html/tutorial.html) and the [full documentation](http://gbeced.github.io/pyalgotrade/docs/v0.16/html/index.html).

Main Features
-------------

 * Event driven.
 * Supports Market, Limit, Stop and StopLimit orders.
 * Supports any type of time-series data in CSV format like Yahoo! Finance, Google Finance, Quandl and NinjaTrader.
 * [Xignite](https://www.xignite.com/) realtime feed.
 * Bitcoin support through [Bitstamp](https://www.bitstamp.net/).
 * Technical indicators and filters like SMA, WMA, EMA, RSI, Bollinger Bands and others.
 * Performance metrics like Sharpe ratio and drawdown analysis.
 * Handling Twitter events in realtime.
 * Event profiler.
 * TA-Lib integration.

Installation
------------

PyAlgoTrade is developed using Python 2.7 and depends on:

 * [NumPy and SciPy](http://numpy.scipy.org/).
 * [pytz](http://pytz.sourceforge.net/).
 * [matplotlib](http://matplotlib.sourceforge.net/) for plotting support.
 * [ws4py](https://github.com/Lawouach/WebSocket-for-Python) for Bitstamp support.
 * [tornado](http://www.tornadoweb.org/en/stable/) for Bitstamp support.
 * [tweepy](https://github.com/tweepy/tweepy) for Twitter support.

You can install PyAlgoTrade using pip like this:

```
pip install pyalgotrade
```

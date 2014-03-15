Introduction
============

PyAlgoTrade is a Python library that I started with one goal in mind: **To make it easy to backtest stock trading strategies**.
This is, given a certain amount of historical data for one stock, I want to check how a certain stock trading strategy behaves.

Although initially designed for backtesting purposes, the design should adapt real trading scenarios and future releases will
gradually support this.

It should also make it easy to optimize a strategy using multiple computers.

PyAlgoTrade is developed using Python 2.7 and depends on:
 * NumPy and SciPy (http://numpy.scipy.org/).
 * pytz (http://pytz.sourceforge.net/).
 * matplotlib (http://matplotlib.sourceforge.net/) for plotting support.
 * ws4py (https://github.com/Lawouach/WebSocket-for-Python) for Bitstamp support.
 * tornado (http://www.tornadoweb.org/en/stable/) for Bitstamp support.
 * tweepy (https://github.com/tweepy/tweepy) for Twitter support.

so you need to have those installed in order to use this library.

You can install PyAlgoTrade using pip like this: ::

    pip install pyalgotrade


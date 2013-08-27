Introduction
============

PyAlgoTrade is a Python library that I started with one goal in mind: **To make it easy to backtest stock trading strategies**.

That is, given a certain amount of historical data for one stock, I want to check how a certain stock trading strategy behaves.
It should also make it easy to optimize a strategy using multiple computers.

PyAlgoTrade is developed using Python 2.7 and depends on:
 * NumPy (http://numpy.scipy.org/)
 * pytz (http://pytz.sourceforge.net/)
 * matplotlib (http://matplotlib.sourceforge.net/)
 * ws4py (https://github.com/Lawouach/WebSocket-for-Python) for MtGox support
 * tornado (http://www.tornadoweb.org/en/stable/) for MtGox support
 * tweepy (https://github.com/tweepy/tweepy) for Twitter support

so you need to have those installed in order to use this library.


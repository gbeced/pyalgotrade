Introduction
============

PyAlgoTrade is an event driven algorithmic trading Python library with support for:
 * Backtesting with historical data from CSV files.
 * Paper trading using :ref:`Bitstamp <bitstamp-tutorial-label>` live feeds.
 * Real trading on Bitstamp.

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


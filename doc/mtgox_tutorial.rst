Tutorial for Bitcoin trading through Mt. Gox
============================================

PyAlgoTrade allows you to backtest and paper trade (backtest using a realtime feed) Bitcoin trading
strategies through Mt. Gox (https://mtgox.com/).

In this tutorial we'll first backtest a trading strategy using historical data, and later on we'll
test it using a realtime feed.
Before we move on, this document assumes that you're already familiar with the basic concepts presented
in the :ref:`tutorial-label` section.

Backtesting
-----------

The first thing that we'll need to test our strategy is some data.
Let's start by downloading trades for January 2013 using the following command::

    python -c "from pyalgotrade.mtgox import tools; tools.download_trades_by_month('USD', 2013, 1, 'trades-mtgox-usd-2013-01.csv')"

The output should look like this: ::

    2013-07-06 00:16:41,893 mtgox [INFO] Downloading trades since 2013-01-01 00:00:00+00:00.
    2013-07-06 00:16:44,058 mtgox [INFO] Got 994 trades.
    2013-07-06 00:16:44,065 mtgox [INFO] Downloading trades since 2013-01-01 17:00:26.229354+00:00.
    2013-07-06 00:16:48,205 mtgox [INFO] Got 998 trades.
    2013-07-06 00:16:48,212 mtgox [INFO] Downloading trades since 2013-01-01 20:32:31.304213+00:00.
    .
    .

and it will take some time since Mt. Gox API returns no more than 1000 trades on each request and there
are about 150218 trades.
The CSV file will have 4 columns:

 * The trade identifier (which is in fact the trade timestamp in microseconds).
 * The price.
 * The amount of bitcoin traded.
 * If the trade is the result of the execution of a bid or an ask.

Let's move on with a simple strategy, that is, one that just prints information from each bar as they are processed:

.. literalinclude:: ../samples/tutorial-mtgox-1.py


The code is doing 4 main things:
 1. Declaring a new strategy. There is only one method that has to be defined, *onBars*, which is called for every bar in the feed.
 2. Loading the feed from a trades CSV file.
 3. Creating a broker for backtesting.
 4. Running the strategy with the bars supplied by the feed and the backtesting broker.

Note that a :class:`pyalgotrade.bar.Bar` instance will be created for every trade in the file.

If you run the script you should see something like this:

.. literalinclude:: ../samples/tutorial-mtgox-1.output



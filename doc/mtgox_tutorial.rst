Tutorial for Bitcoin trading through Mt. Gox
============================================

MtGox support depends on **ws4py** (https://github.com/Lawouach/WebSocket-for-Python) 
and **tornado** (http://www.tornadoweb.org/en/stable/)
so be sure to have those installed before moving forward.

PyAlgoTrade allows you to backtest and paper trade (backtest using a realtime feed) Bitcoin trading
strategies through Mt. Gox (https://mtgox.com/).

In this tutorial we'll first backtest a trading strategy using historical data, and later on we'll
test it using a realtime feed.
Before we move on, this tutorial assumes that you're already familiar with the basic concepts presented
in the :ref:`tutorial-label` section.

Backtesting
-----------

The first thing that we'll need to test our strategy is some data.
Let's start by downloading trades for March 2013 using the following command::

    python -c "from pyalgotrade.mtgox import tools; tools.download_trades_by_month('USD', 2013, 3, 'trades-mtgox-usd-2013-03.csv')"

The output should look like this: ::

    2013-08-12 22:34:22,260 mtgox [INFO] Downloading trades since 2013-03-01 00:00:00+00:00.
    2013-08-12 22:34:25,728 mtgox [INFO] Got 1000 trades.
    2013-08-12 22:34:25,739 mtgox [INFO] Downloading trades since 2013-03-01 05:06:22.262840+00:00.
    2013-08-12 22:34:27,581 mtgox [INFO] Got 1000 trades.
    2013-08-12 22:34:27,594 mtgox [INFO] Downloading trades since 2013-03-01 09:03:12.939311+00:00.
    2013-08-12 22:34:29,307 mtgox [INFO] Got 1000 trades.
    2013-08-12 22:34:29,319 mtgox [INFO] Downloading trades since 2013-03-01 11:35:16.695161+00:00.
    2013-08-12 22:34:30,954 mtgox [INFO] Got 1000 trades.
    2013-08-12 22:34:30,966 mtgox [INFO] Downloading trades since 2013-03-01 15:55:48.855317+00:00.
    2013-08-12 22:34:32,679 mtgox [INFO] Got 1000 trades.
    2013-08-12 22:34:32,691 mtgox [INFO] Downloading trades since 2013-03-01 18:19:12.283606+00:00.
    .
    .

and it will take some time since Mt. Gox API returns no more than 1000 trades on each request and there
are about 324878 trades.
The CSV file will have 4 columns:

 * The trade identifier (which is in fact the trade timestamp in microseconds).
 * The price.
 * The amount of bitcoin traded.
 * If the trade is the result of the execution of a bid or an ask.

For this tutorial we'll use a Bitcoin Scalper strategy inspired in http://nobulart.com/bitcoin/blog/bitcoin-scalper-part-1/ .
As explained in that webpage, the general idea is to place a bid order a fixed percentage below the current market price.
Once a bid order is filled, it is transitioned to the held state. It will remain held until any one of the following three conditions are met:
 
 * The commit price is met
 * The stop loss is triggered
 * The maximum hold period is exceeded

Depending on which condition was met, we'll exit with a Market or a Limit order.

Save the following code as **mtgox_scalper.py**.

.. literalinclude:: ../samples/mtgox_scalper.py

and use the following code to run the **mtgox_scalper.py** strategy with the bars we just downloaded:

.. literalinclude:: ../samples/tutorial_mtgox_1.py

The code is doing 3 things:
 1. Loading the feed from a trades CSV file. Note that a :class:`pyalgotrade.bar.Bar` instance will be created for every trade in the file.
 2. Creating a broker for backtesting. The broker will charge a 0.6 % fee for each order.
 3. Running the strategy with the bars supplied by the feed and the backtesting broker, and optionally plotting some figures.

If you run the script you should see something like this:

.. literalinclude:: ../samples/tutorial_mtgox_1.output

.. image:: ../samples/tutorial_mtgox_1.png

Note that while this strategy seems profitable for March 2013, it may not be the case for other periods. The main point of this
tutorial is to show how to build and run a strategy.

Papertrading
------------

Now let's run the same strategy but instead of using historical data we'll use live data coming directly from MtGox:

.. literalinclude:: ../samples/tutorial_mtgox_2.py

The code is doing 4 things:
 1. Creating a client to connect to MtGox. For papertrading purposes we only need to specify the currency to use.
 2. Creating a live feed that will build bars from the trades received through the client.
 3. Creating a broker for backtesting. The broker will charge a 0.6 % fee for each order.
 4. Running the strategy with the bars supplied by the feed and the backtesting broker. Note that we had to add the client to the event dispatch loop before running the strategy.

If you run the script you should see something like this:

.. literalinclude:: ../samples/tutorial_mtgox_2.output


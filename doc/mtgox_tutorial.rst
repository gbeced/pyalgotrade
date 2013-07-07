Tutorial for Bitcoin trading through Mt. Gox
============================================

PyAlgoTrade allows you to backtest and paper trade (backtest using a realtime feed) Bitcoin trading
strategies through Mt. Gox (https://mtgox.com/).

In this tutorial we'll first backtest a trading strategy using historical data, and later on we'll
test it using a realtime feed.

Backtesting
-----------

The first thing that we'll need to test our strategy is some data.
Let's start by downloading trades for January and February 2013 using the following commands::

    python -c "from pyalgotrade.mtgox import tools; tools.download_trades_by_month('USD', 2013, 1, 'trades-mgtox-usd-2013-01.csv')"
    python -c "from pyalgotrade.mtgox import tools; tools.download_trades_by_month('USD', 2013, 2, 'trades-mgtox-usd-2013-02.csv')"

The output should look like this: ::

    2013-07-06 00:16:41,893 mtgox [INFO] Downloading trades since 2013-01-01 00:00:00+00:00.
    2013-07-06 00:16:44,058 mtgox [INFO] Got 994 trades.
    2013-07-06 00:16:44,065 mtgox [INFO] Downloading trades since 2013-01-01 17:00:26.229354+00:00.
    2013-07-06 00:16:48,205 mtgox [INFO] Got 998 trades.
    2013-07-06 00:16:48,212 mtgox [INFO] Downloading trades since 2013-01-01 20:32:31.304213+00:00.
    .
    .

and it will take some time since Mt. Gox API returns no more than 1000 trades on each request.
The CSV files will have 4 columns:

 * The trade identifier (which is in fact the trade timestamp in microseconds).
 * The price.
 * The amount of bitcoin traded.
 * If the trade is the result of the execution of a bid or an ask.


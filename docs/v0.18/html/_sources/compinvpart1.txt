Computational Investing Part I
==============================

As I was taking the `Computational Investing Part I <https://class.coursera.org/compinvesting1-2012-001/class>`_ course in 2012
I had to work on a set of assignments and for some of them I used PyAlgoTrade.

Homework 1
----------

For this assignment I had to pick 4 stocks, invest a total of $100000 during 2011, and calculate:

 * Final portfolio value
 * Anual return
 * Average daily return
 * Std. dev. of daily returns
 * Sharpe ratio

Download the data with the following commands: ::

    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('aeti', 2011, 'aeti-2011-yahoofinance.csv')"
    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('egan', 2011, 'egan-2011-yahoofinance.csv')"
    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('glng', 2011, 'glng-2011-yahoofinance.csv')"
    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('simo', 2011, 'simo-2011-yahoofinance.csv')"

Although the deliverable was an Excel spreadsheet, I validated the results using this piece of code:

.. literalinclude:: ../samples/compinv-1.py

The results were:

.. literalinclude:: ../samples/compinv-1.output

Homework 3 and 4
----------------

For these assignments I had to build a market simulation tool that loads orders from a file, executes those,
and prints the results for each day.

The orders file for homework 3 look like this: ::

    2011,1,10,AAPL,Buy,1500,
    2011,1,13,AAPL,Sell,1500,
    2011,1,13,IBM,Buy,4000,
    2011,1,26,GOOG,Buy,1000,
    2011,2,2,XOM,Sell,4000,
    2011,2,10,XOM,Buy,4000,
    2011,3,3,GOOG,Sell,1000,
    2011,3,3,IBM,Sell,2200,
    2011,6,3,IBM,Sell,3300,
    2011,5,3,IBM,Buy,1500,
    2011,6,10,AAPL,Buy,1200,
    2011,8,1,GOOG,Buy,55,
    2011,8,1,GOOG,Sell,55,
    2011,12,20,AAPL,Sell,1200,

This is the market simulation tool that I built:

.. literalinclude:: ../samples/compinv-3.py

The output for homework 3 looks like this: ::

    First date 2011-01-10 00:00:00
    Last date 2011-12-20 00:00:00
    Symbols ['AAPL', 'IBM', 'GOOG', 'XOM']
    2011-01-10 00:00:00: Portfolio value: $1000000.00
    2011-01-11 00:00:00: Portfolio value: $998785.00
    2011-01-12 00:00:00: Portfolio value: $1002940.00
    2011-01-13 00:00:00: Portfolio value: $1004815.00
    .
    .
    .
    2011-12-15 00:00:00: Portfolio value: $1113532.00
    2011-12-16 00:00:00: Portfolio value: $1116016.00
    2011-12-19 00:00:00: Portfolio value: $1117444.00
    2011-12-20 00:00:00: Portfolio value: $1133860.00
    Final portfolio value: $1133860.00
    Anual return: 13.39 %
    Average daily return: 0.05 %
    Std. dev. daily return: 0.0072
    Sharpe ratio: 1.21


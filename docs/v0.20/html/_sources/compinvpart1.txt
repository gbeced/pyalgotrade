Computational Investing Part I
==============================

As I was taking the `Computational Investing Part I <https://class.coursera.org/compinvesting1-2012-001/class>`_ course in 2012
I had to work on a set of assignments and for one of them I used PyAlgoTrade.

Homework 1
----------

For this assignment I had to pick 4 stocks, invest a total of $1000000 during 2011, and calculate:

 * Final portfolio value
 * Anual return
 * Average daily return
 * Std. dev. of daily returns
 * Sharpe ratio

Download the data with the following commands: ::

    python -m "pyalgotrade.tools.quandl" --source-code="WIKI" --table-code="IBM" --from-year=2011 --to-year=2011 --storage=. --force-download --frequency=daily
    python -m "pyalgotrade.tools.quandl" --source-code="WIKI" --table-code="AES" --from-year=2011 --to-year=2011 --storage=. --force-download --frequency=daily
    python -m "pyalgotrade.tools.quandl" --source-code="WIKI" --table-code="AIG" --from-year=2011 --to-year=2011 --storage=. --force-download --frequency=daily
    python -m "pyalgotrade.tools.quandl" --source-code="WIKI" --table-code="ORCL" --from-year=2011 --to-year=2011 --storage=. --force-download --frequency=daily

Although the deliverable was an Excel spreadsheet, I validated the results using this piece of code:

.. literalinclude:: ../samples/compinv-1.py

The results were:

.. literalinclude:: ../samples/compinv-1.output

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

Although the deliverable was an Excel spreadsheet, I validated the results using this piece of code:

.. literalinclude:: ../samples/compinv-1.py

The results were: ::

    Final portfolio value: $2917766.47
    Anual return: 191.78 %
    Average daily return: 0.44 %
    Std. dev. daily return: 0.0186
    Sharpe ratio: 3.78


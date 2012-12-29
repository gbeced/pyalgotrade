stratanalyzer -- Strategy analyzers
===================================

Strategy analyzers provide an extensible way to attach different calculations to strategy executions.

.. automodule:: pyalgotrade.stratanalyzer
    :members: StrategyAnalyzer

Returns
-------
.. automodule:: pyalgotrade.stratanalyzer.returns
    :members: Returns

Sharpe Ratio
------------
.. automodule:: pyalgotrade.stratanalyzer.sharpe
    :members: SharpeRatio

DrawDown
--------
.. automodule:: pyalgotrade.stratanalyzer.drawdown
    :members: DrawDown

Trades
------
.. automodule:: pyalgotrade.stratanalyzer.trades
    :members: Trades
    :member-order: bysource

Example
-------
This example depends on smacross_strategy.py from the tutorial section.

.. literalinclude:: ../samples/sample-strategy-analyzer.py

The output should look like this: ::

    Final portfolio value: $1124.90
    Cumulative returns: 12.49 %
    Sharpe ratio: 0.39
    Max. drawdown: 17.85 %
    Max. drawdown duration: 193 days

    Total trades: 11
    Avg. profit: $ 9
    Profits std. dev.: $66
    Max. profit: $186
    Min. profit: $-58
    Avg. return:  2 %
    Returns std. dev.: 10 %
    Max. return: 30 %
    Min. return: -7 %

    Profitable trades: 3
    Avg. profit: $101
    Profits std. dev.: $61
    Max. profit: $186
    Min. profit: $47
    Avg. return: 15 %
    Returns std. dev.: 11 %
    Max. return: 30 %
    Min. return:  6 %

    Unprofitable trades: 8
    Avg. loss: $-26
    Losses std. dev.: $17
    Max. loss: $-58
    Min. loss: $-3
    Avg. return: -3 %
    Returns std. dev.:  2 %
    Max. return: -0 %
    Min. return: -7 %

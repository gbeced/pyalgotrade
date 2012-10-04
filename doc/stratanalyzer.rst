stratanalyzer -- Strategy analyzers
===================================

Strategy analyzers provide an extensible way to attach different calculations to strategy executions.

.. automodule:: pyalgotrade.stratanalyzer
    :members: StrategyAnalyzer

Returns
-------
.. automodule:: pyalgotrade.stratanalyzer.returns
    :members: ReturnsAnalyzer, ReturnsDataSeries, CumulativeReturnsDataSeries

Sharpe Ratio
------------
.. automodule:: pyalgotrade.stratanalyzer.sharpe
    :members: SharpeRatio

DrawDown
--------
.. automodule:: pyalgotrade.stratanalyzer.drawdown
    :members: DrawDown

Example
-------
.. literalinclude:: ../samples/sample-strategy-analyzer.py

The output should look like this: ::

    Final portfolio value: $1124.90
    Cumulative returns: 28.13 %
    Sharpe ratio: 0.66
    Max. drawdown: 24.77 %
    Max. drawdown duration: 193 days


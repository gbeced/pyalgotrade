stratanalyzer -- Strategy analyzers
===================================

Strategy analyzers provide an extensible way to attach different calculations to strategy executions.

.. automodule:: pyalgotrade.stratanalyzer
    :members: StrategyAnalyzer
    :show-inheritance:

Returns
-------
.. automodule:: pyalgotrade.stratanalyzer.returns
    :members: Returns
    :show-inheritance:

Sharpe Ratio
------------
.. automodule:: pyalgotrade.stratanalyzer.sharpe
    :members: SharpeRatio
    :show-inheritance:

DrawDown
--------
.. automodule:: pyalgotrade.stratanalyzer.drawdown
    :members: DrawDown
    :show-inheritance:

Trades
------
.. automodule:: pyalgotrade.stratanalyzer.trades
    :members: Trades
    :member-order: bysource
    :show-inheritance:

Example
-------
Save this code as sma_crossover.py:

.. literalinclude:: ../samples/sma_crossover.py

and save this code in a different file:

.. literalinclude:: ../samples/sample-strategy-analyzer.py

The output should look like this:

.. literalinclude:: ../samples/sample-strategy-analyzer.output

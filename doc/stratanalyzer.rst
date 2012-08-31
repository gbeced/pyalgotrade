stratanalyzer -- Strategy analyzers
===================================

.. automodule:: pyalgotrade.stratanalyzer
    :members: StrategyAnalyzer

.. automodule:: pyalgotrade.stratanalyzer.trades
    :members: WinningLosingTrades

WinningLosingTrades Example
---------------------------
::

    from pyalgotrade.stratanalyzer import trades

    strat = MyStrategy(...)
    stratAnalyzer = trades.WinningLosingTrades()
    strat.attachAnalyzer(stratAnalyzer)
    strat.run()

    stratAnalyzer.getTotalTrades()

    stratAnalyzer.getWinningTrades()
    stratAnalyzer.getWinningTradesMean()
    stratAnalyzer.getWinningTradesStdDev()

    stratAnalyzer.getLosingTrades()
    stratAnalyzer.getLosingTradesMean()
    stratAnalyzer.getLosingTradesStdDev()


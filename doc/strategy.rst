strategy -- Basic strategy classes
==================================

Strategies are the classes that you define that implement the trading logic, when to buy, when to sell, etc.
Buying and selling can be done in several ways:

    * Using any of the following methods:

     * :meth:`pyalgotrade.strategy.BaseStrategy.marketOrder`
     * :meth:`pyalgotrade.strategy.BaseStrategy.limitOrder`
     * :meth:`pyalgotrade.strategy.BaseStrategy.stopOrder`
     * :meth:`pyalgotrade.strategy.BaseStrategy.stopLimitOrder`

    * Using a long/short position based interface:

     * :meth:`pyalgotrade.strategy.BaseStrategy.enterLong`
     * :meth:`pyalgotrade.strategy.BaseStrategy.enterShort`
     * :meth:`pyalgotrade.strategy.BaseStrategy.enterLongLimit`
     * :meth:`pyalgotrade.strategy.BaseStrategy.enterShortLimit`

Positions are higher level abstractions for placing orders.
They are escentially a pair of entry-exit orders and allow
tracking returns and PnL easier than placing individual orders.


Strategy
--------

.. automodule:: pyalgotrade.strategy
    :members: BaseStrategy, BacktestingStrategy
    :show-inheritance:
    :member-order: bysource

Position
--------

.. automodule:: pyalgotrade.strategy.position
    :members: Position
    :show-inheritance:
    :member-order: bysource

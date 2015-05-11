strategy -- Basic strategy classes
==================================

Strategies are the classes that you define that implement the trading logic, when to buy, when to sell, etc.

Buying and selling can be done in two ways:

    * Placing individual orders using any of the following methods:

     * :meth:`pyalgotrade.strategy.BaseStrategy.marketOrder`
     * :meth:`pyalgotrade.strategy.BaseStrategy.limitOrder`
     * :meth:`pyalgotrade.strategy.BaseStrategy.stopOrder`
     * :meth:`pyalgotrade.strategy.BaseStrategy.stopLimitOrder`

    * Using a higher level interface that wrap a pair of entry/exit orders:

     * :meth:`pyalgotrade.strategy.BaseStrategy.enterLong`
     * :meth:`pyalgotrade.strategy.BaseStrategy.enterShort`
     * :meth:`pyalgotrade.strategy.BaseStrategy.enterLongLimit`
     * :meth:`pyalgotrade.strategy.BaseStrategy.enterShortLimit`

Positions are higher level abstractions for placing orders. They are escentially a pair of entry-exit orders and provide
easier tracking for returns and PnL than using individual orders.


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

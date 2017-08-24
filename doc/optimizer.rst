optimizer -- Parallel optimizers
================================

.. automodule:: pyalgotrade.optimizer.server
    :members:
    :member-order: bysource
    :show-inheritance:

.. automodule:: pyalgotrade.optimizer.worker
    :members:
    :member-order: bysource
    :show-inheritance:

.. automodule:: pyalgotrade.optimizer.local
    :members:
    :member-order: bysource
    :show-inheritance:

.. note::
    * The server component will split strategy executions in chunks which are distributed among the different workers. You can optionally set the chunk size by passing in **batchSize** to the constructor of **pyalgotrade.optimizer.xmlrpcserver.Server**.
    * The :meth:`pyalgotrade.strategy.BaseStrategy.getResult` method is used to select the best strategy execution. You can override that method to rank executions using a different criteria.


feed -- Basic feeds
===================

Feeds are time series data providing abstractions.
When these are included in the event dispatch loop, they emit an event as new data is available.
Feeds are also responsible for updating the :class:`pyalgotrade.dataseries.DataSeries` associated 
with each piece of data that the feed provides.

**This package has basic feeds. For bar feeds refer to the** :ref:`barfeed-label` **section.**

.. automodule:: pyalgotrade.feed
    :members: BaseFeed
    :special-members:
    :exclude-members: __weakref__
    :show-inheritance:

CSV support
-----------

.. automodule:: pyalgotrade.feed.csvfeed
    :members: Feed
    :special-members:
    :exclude-members: __weakref__
    :show-inheritance:

CSV support Example
-------------------
A file with the following format ::

    Date,USD,GBP,EUR
    2013-09-29,1333.0,831.203,986.75
    2013-09-22,1349.25,842.755,997.671
    2013-09-15,1318.5,831.546,993.969
    2013-09-08,1387.0,886.885,1052.911
    .
    .
    .

can be loaded like this:

.. literalinclude:: ../samples/csvfeed_1.py

and the output should look like this:

.. literalinclude:: ../samples/csvfeed_1.output


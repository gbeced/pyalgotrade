dataseries -- Basic dataseries classes
======================================

.. automodule:: pyalgotrade.dataseries
    :members: DataSeries, SequenceDataSeries, BarDataSeries

Example
-------

::

    from pyalgotrade import dataseries

    # Build a sequence based DataSeries.
    ds = dataseries.SequenceDataSeries(range(0, 50))

    # Get the last value.
    print ds.getValue()
    print ds.getValueAbsolute(49)

    # Get the previous value.
    print ds.getValue(1)
    print ds.getValueAbsolute(48)

    # Get the first value.
    print ds.getValue(49)
    print ds.getValueAbsolute(0)

The output should be: ::

    49
    49
    48
    48
    0
    0


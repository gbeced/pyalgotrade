RSI2
====

This example is based on a strategy known as RSI2 (http://stockcharts.com/school/doku.php?id=chart_school:trading_strategies:rsi2)
which requires the following parameters:

 * An SMA period for trend identification. We’ll call this entrySMA.
 * A smaller SMA period for the exit point. We’ll call this exitSMA.
 * An RSI period for entering both short/long positions. We’ll call this rsiPeriod.
 * An RSI oversold threshold for long position entry. We’ll call this overSoldThreshold.
 * An RSI overbought threshold for short position entry. We’ll call this overBoughtThreshold.

Save this code as rsi2.py:

.. literalinclude:: ../samples/rsi2.py

and use the following code to execute the strategy:

.. literalinclude:: ../samples/rsi2_sample.py

This is what the output should look like:

.. literalinclude:: ../samples/rsi2_sample.output

and this is what the plot should look like:

.. image:: ../samples/rsi2_sample.png

You can get better returns by tunning the different parameters.

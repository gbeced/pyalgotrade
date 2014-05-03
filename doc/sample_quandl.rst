Quandl integration
==================

The purpose of this example is to show how to integrate price data along with any
time-series data in CSV format from Quandl into a strategy.

We'll use the following CSV data from Quandl:
http://www.quandl.com/OFDP-Open-Financial-Data-Project/GOLD_2-LBMA-Gold-Price-London-Fixings-P-M

.. literalinclude:: ../samples/quandl_sample.py

This is what the output should look like:

.. literalinclude:: ../samples/quandl_sample.output

and this is what the plot should look like:

.. image:: ../samples/quandl_sample.png

import numpy as np
from pyalgotrade import technical
from pyalgotrade.technical import ma

class MAD(technical.EventBasedFilter):
    """Moving Average Distance filter.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param fast_period: The number of values to use to calculate the MAD.
    :type period: int.
    :param slow_period: The number of values to use to calculate the MAD.
    :type period: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, dataSeries, fast_period=21, slow_period=200, maxLen=None):
        
        self.__sma_fast = ma.SMA(dataSeries, fast_period, maxLen=maxLen)
        self.__sma_slow = ma.SMA(dataSeries, slow_period, maxLen=maxLen)
        
        self.__mad = dataseries.SequenceDataSeries(maxLen)
        
        # It is important to subscribe after sma and stddev since we'll use those values.
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)
        
    def __onNewValue(self, dateTime, value):
        
        mad = None 

        if value is not None:
            self.sma_fast = self.__sma[-1]
            self.sma_slow = self.__sma[-1]
            if self.sma_fast != None and self.sma_slow != None: 
                mad = self.sma_fast / self.sma_slow  
                     
        self.__mad.appendWithDateTime(dateTime, mad)
        
    def getValue(self):
        return self.__mad[-1]


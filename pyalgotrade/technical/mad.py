import numpy as np
from pyalgotrade import dataseries
from pyalgotrade import technical
from pyalgotrade.technical import ma

class MAD(object):
    """Moving Average Distance

    :param dataSeries: The DataSeries instance being filtered for the SMAs in MAD.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param fastSMA_period: The number of values to use to calculate the MAD.
    :type period: int.
    :param slowSMA_period: The number of values to use to calculate the MAD.
    :type period: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, dataSeries, fastSMA_period=21, slowSMA_period=200, maxLen=None):
        
        self.__sma_fast = ma.SMA(dataSeries, fastSMA_period, maxLen=maxLen)
        self.__sma_slow = ma.SMA(dataSeries, slowSMA_period, maxLen=maxLen)
        
        self.__mad = dataseries.SequenceDataSeries(maxLen)
        
        # It is important to subscribe after sma and stddev since we'll use those values.
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)
        
        
    def __onNewValue(self, dataseries, dateTime, value):
        
        self.mad = None 

        if value is not None and not np.isnan(value):
            self.sma_fast = self.__sma_fast[-1]
            self.sma_slow = self.__sma_slow[-1]
            if self.sma_fast != None and self.sma_slow != None: 
                self.mad = self.sma_fast / self.sma_slow  
        self.__mad.appendWithDateTime(dateTime, self.mad)
        
    def getValue(self):
        return self.mad


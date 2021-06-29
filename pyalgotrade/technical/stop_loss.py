from pyalgotrade import dataseries
from pyalgotrade import technical
from pyalgotrade.utils import collections
from pyalgotrade.utils import dt

class StopLoss(dataseries.SequenceDataSeries):
    def __init__(self, dataSeries, max_loss, maxLen=None):
        super(StopLoss, self).__init__(maxLen)
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    # def __onNewValue(self, dataSeries, dateTime, value):
        # diff


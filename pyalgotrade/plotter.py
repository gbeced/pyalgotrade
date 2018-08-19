# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import collections

import matplotlib.pyplot as plt
from matplotlib import ticker
import six

from pyalgotrade import broker
from pyalgotrade import warninghelpers


def get_last_value(dataSeries):
    ret = None
    try:
        ret = dataSeries[-1]
    except IndexError:
        pass
    return ret


def _filter_datetimes(dateTimes, fromDate=None, toDate=None):
    class DateTimeFilter(object):
        def __init__(self, fromDate=None, toDate=None):
            self.__fromDate = fromDate
            self.__toDate = toDate

        def includeDateTime(self, dateTime):
            if self.__toDate and dateTime > self.__toDate:
                return False
            if self.__fromDate and dateTime < self.__fromDate:
                return False
            return True

    dateTimeFilter = DateTimeFilter(fromDate, toDate)
    return [x for x in dateTimes if dateTimeFilter.includeDateTime(x)]


def _post_plot_fun(subPlot, mplSubplot):
    # Legend
    mplSubplot.legend(list(subPlot.getAllSeries().keys()), shadow=True, loc="best")
    # Don't scale the Y axis
    mplSubplot.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))


class Series(object):
    def __init__(self):
        self.__values = {}

    def getColor(self):
        return None

    def addValue(self, dateTime, value):
        self.__values[dateTime] = value

    def getValue(self, dateTime):
        return self.__values.get(dateTime, None)

    def getValues(self):
        return self.__values

    def getMarker(self):
        raise NotImplementedError()

    def needColor(self):
        raise NotImplementedError()

    def plot(self, mplSubplot, dateTimes, color):
        values = []
        for dateTime in dateTimes:
            values.append(self.getValue(dateTime))
        mplSubplot.plot(dateTimes, values, color=color, marker=self.getMarker())


class BuyMarker(Series):
    def getColor(self):
        return 'g'

    def getMarker(self):
        return "^"

    def needColor(self):
        return True


class SellMarker(Series):
    def getColor(self):
        return 'r'

    def getMarker(self):
        return "v"

    def needColor(self):
        return True


class CustomMarker(Series):
    def __init__(self):
        super(CustomMarker, self).__init__()
        self.__marker = "o"

    def needColor(self):
        return True

    def setMarker(self, marker):
        self.__marker = marker

    def getMarker(self):
        return self.__marker


class LineMarker(Series):
    def __init__(self):
        super(LineMarker, self).__init__()
        self.__marker = " "

    def needColor(self):
        return True

    def setMarker(self, marker):
        self.__marker = marker

    def getMarker(self):
        return self.__marker


class InstrumentMarker(Series):
    def __init__(self):
        super(InstrumentMarker, self).__init__()
        self.__useAdjClose = None
        self.__marker = " "

    def needColor(self):
        return True

    def setMarker(self, marker):
        self.__marker = marker

    def getMarker(self):
        return self.__marker

    def setUseAdjClose(self, useAdjClose):
        # Force close/adj_close instead of price.
        self.__useAdjClose = useAdjClose

    def getValue(self, dateTime):
        # If not using candlesticks, the return the closing price.
        ret = Series.getValue(self, dateTime)
        if ret is not None:
            if self.__useAdjClose is None:
                ret = ret.getPrice()
            elif self.__useAdjClose:
                ret = ret.getAdjClose()
            else:
                ret = ret.getClose()
        return ret


class HistogramMarker(Series):
    def needColor(self):
        return True

    def getColorForValue(self, value, default):
        return default

    def plot(self, mplSubplot, dateTimes, color):
        validDateTimes = []
        values = []
        colors = []
        for dateTime in dateTimes:
            value = self.getValue(dateTime)
            if value is not None:
                validDateTimes.append(dateTime)
                values.append(value)
                colors.append(self.getColorForValue(value, color))
        mplSubplot.bar(validDateTimes, values, color=colors)


class MACDMarker(HistogramMarker):
    def getColorForValue(self, value, default):
        ret = default
        if value >= 0:
            ret = "g"
        else:
            ret = "r"
        return ret


class Subplot(object):
    """ """
    colors = ['b', 'c', 'm', 'y', 'k']

    def __init__(self):
        self.__series = {}  # Series by name.
        self.__callbacks = {}  # Maps a function to a Series.
        self.__nextColor = 0

    def __getColor(self, series):
        ret = series.getColor()
        if ret is None:
            ret = Subplot.colors[self.__nextColor % len(Subplot.colors)]
            self.__nextColor += 1
        return ret

    def isEmpty(self):
        return len(self.__series) == 0

    def getAllSeries(self):
        return self.__series

    def addDataSeries(self, label, dataSeries, defaultClass=LineMarker):
        """Add a DataSeries to the subplot.

        :param label: A name for the DataSeries values.
        :type label: string.
        :param dataSeries: The DataSeries to add.
        :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
        """
        callback = lambda bars: get_last_value(dataSeries)
        self.__callbacks[callback] = self.getSeries(label, defaultClass)

    def addCallback(self, label, callback, defaultClass=LineMarker):
        """Add a callback that will be called on each bar.

        :param label: A name for the series values.
        :type label: string.
        :param callback: A function that receives a :class:`pyalgotrade.bar.Bars` instance as a parameter and returns a number or None.
        """
        self.__callbacks[callback] = self.getSeries(label, defaultClass)

    def addLine(self, label, level):
        """Add a horizontal line to the plot.

        :param label: A label.
        :type label: string.
        :param level: The position for the line.
        :type level: int/float.
        """
        self.addCallback(label, lambda x: level)

    def onBars(self, bars):
        dateTime = bars.getDateTime()
        for cb, series in six.iteritems(self.__callbacks):
            series.addValue(dateTime, cb(bars))

    def getSeries(self, name, defaultClass=LineMarker):
        try:
            ret = self.__series[name]
        except KeyError:
            ret = defaultClass()
            self.__series[name] = ret
        return ret

    def getCustomMarksSeries(self, name):
        return self.getSeries(name, CustomMarker)

    def plot(self, mplSubplot, dateTimes, postPlotFun=_post_plot_fun):
        for series in self.__series.values():
            color = None
            if series.needColor():
                color = self.__getColor(series)
            series.plot(mplSubplot, dateTimes, color)

        postPlotFun(self, mplSubplot)


class InstrumentSubplot(Subplot):
    """A Subplot responsible for plotting an instrument."""
    def __init__(self, instrument, plotBuySell):
        super(InstrumentSubplot, self).__init__()
        self.__instrument = instrument
        self.__plotBuySell = plotBuySell
        self.__instrumentSeries = self.getSeries(instrument, InstrumentMarker)

    def setUseAdjClose(self, useAdjClose):
        self.__instrumentSeries.setUseAdjClose(useAdjClose)

    def onBars(self, bars):
        super(InstrumentSubplot, self).onBars(bars)
        bar = bars.getBar(self.__instrument)
        if bar:
            dateTime = bars.getDateTime()
            self.__instrumentSeries.addValue(dateTime, bar)

    def onOrderEvent(self, broker_, orderEvent):
        order = orderEvent.getOrder()
        if self.__plotBuySell and orderEvent.getEventType() in (broker.OrderEvent.Type.PARTIALLY_FILLED, broker.OrderEvent.Type.FILLED) and order.getInstrument() == self.__instrument:
            action = order.getAction()
            execInfo = orderEvent.getEventInfo()
            if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
                self.getSeries("Buy", BuyMarker).addValue(execInfo.getDateTime(), execInfo.getPrice())
            elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
                self.getSeries("Sell", SellMarker).addValue(execInfo.getDateTime(), execInfo.getPrice())


class StrategyPlotter(object):
    """Class responsible for plotting a strategy execution.

    :param strat: The strategy to plot.
    :type strat: :class:`pyalgotrade.strategy.BaseStrategy`.
    :param plotAllInstruments: Set to True to get a subplot for each instrument available.
    :type plotAllInstruments: boolean.
    :param plotBuySell: Set to True to get the buy/sell events plotted for each instrument available.
    :type plotBuySell: boolean.
    :param plotPortfolio: Set to True to get the portfolio value (shares + cash) plotted.
    :type plotPortfolio: boolean.
    """

    def __init__(self, strat, plotAllInstruments=True, plotBuySell=True, plotPortfolio=True):
        self.__dateTimes = set()

        self.__plotAllInstruments = plotAllInstruments
        self.__plotBuySell = plotBuySell
        self.__barSubplots = {}
        self.__namedSubplots = collections.OrderedDict()
        self.__portfolioSubplot = None
        if plotPortfolio:
            self.__portfolioSubplot = Subplot()

        strat.getBarsProcessedEvent().subscribe(self.__onBarsProcessed)
        strat.getBroker().getOrderUpdatedEvent().subscribe(self.__onOrderEvent)

    def __checkCreateInstrumentSubplot(self, instrument):
        if instrument not in self.__barSubplots:
            self.getInstrumentSubplot(instrument)

    def __onBarsProcessed(self, strat, bars):
        dateTime = bars.getDateTime()
        self.__dateTimes.add(dateTime)

        if self.__plotAllInstruments:
            for instrument in bars.getInstruments():
                self.__checkCreateInstrumentSubplot(instrument)

        # Notify named subplots.
        for subplot in self.__namedSubplots.values():
            subplot.onBars(bars)

        # Notify bar subplots.
        for subplot in self.__barSubplots.values():
            subplot.onBars(bars)

        # Feed the portfolio evolution subplot.
        if self.__portfolioSubplot:
            self.__portfolioSubplot.getSeries("Portfolio").addValue(dateTime, strat.getBroker().getEquity())
            # This is in case additional dataseries were added to the portfolio subplot.
            self.__portfolioSubplot.onBars(bars)

    def __onOrderEvent(self, broker_, orderEvent):
        # Notify BarSubplots
        for subplot in self.__barSubplots.values():
            subplot.onOrderEvent(broker_, orderEvent)

    def getInstrumentSubplot(self, instrument):
        """Returns the InstrumentSubplot for a given instrument

        :rtype: :class:`InstrumentSubplot`.
        """
        try:
            ret = self.__barSubplots[instrument]
        except KeyError:
            ret = InstrumentSubplot(instrument, self.__plotBuySell)
            self.__barSubplots[instrument] = ret
        return ret

    def getOrCreateSubplot(self, name):
        """Returns a Subplot by name. If the subplot doesn't exist, it gets created.

        :param name: The name of the Subplot to get or create.
        :type name: string.
        :rtype: :class:`Subplot`.
        """
        try:
            ret = self.__namedSubplots[name]
        except KeyError:
            ret = Subplot()
            self.__namedSubplots[name] = ret
        return ret

    def getPortfolioSubplot(self):
        """Returns the subplot where the portfolio values get plotted.

        :rtype: :class:`Subplot`.
        """
        return self.__portfolioSubplot

    def __buildFigureImpl(self, fromDateTime=None, toDateTime=None, postPlotFun=_post_plot_fun):
        dateTimes = _filter_datetimes(self.__dateTimes, fromDateTime, toDateTime)
        dateTimes.sort()

        subplots = []
        subplots.extend(self.__barSubplots.values())
        subplots.extend(self.__namedSubplots.values())
        if self.__portfolioSubplot is not None:
            subplots.append(self.__portfolioSubplot)

        # Build each subplot.
        fig, axes = plt.subplots(nrows=len(subplots), sharex=True, squeeze=False)
        mplSubplots = []
        for i, subplot in enumerate(subplots):
            axesSubplot = axes[i][0]
            if not subplot.isEmpty():
                mplSubplots.append(axesSubplot)
                subplot.plot(axesSubplot, dateTimes, postPlotFun=postPlotFun)
                axesSubplot.grid(True)

        return (fig, mplSubplots)

    def buildFigure(self, fromDateTime=None, toDateTime=None):
        # Deprecated in v0.18.
        warninghelpers.deprecation_warning("buildFigure will be deprecated in the next version. Use buildFigureAndSubplots.", stacklevel=2)

        fig, _ = self.buildFigureAndSubplots(fromDateTime, toDateTime)
        return fig

    def buildFigureAndSubplots(self, fromDateTime=None, toDateTime=None, postPlotFun=_post_plot_fun):
        """
        Build a matplotlib.figure.Figure with the subplots. Must be called after running the strategy.

        :param fromDateTime: An optional starting datetime.datetime. Everything before it won't get plotted.
        :type fromDateTime: datetime.datetime
        :param toDateTime: An optional ending datetime.datetime. Everything after it won't get plotted.
        :type toDateTime: datetime.datetime
        :rtype: A 2 element tuple with matplotlib.figure.Figure and subplots.
        """
        fig, mplSubplots = self.__buildFigureImpl(fromDateTime, toDateTime, postPlotFun=postPlotFun)
        fig.autofmt_xdate()
        return fig, mplSubplots

    def plot(self, fromDateTime=None, toDateTime=None, postPlotFun=_post_plot_fun):
        """
        Plot the strategy execution. Must be called after running the strategy.

        :param fromDateTime: An optional starting datetime.datetime. Everything before it won't get plotted.
        :type fromDateTime: datetime.datetime
        :param toDateTime: An optional ending datetime.datetime. Everything after it won't get plotted.
        :type toDateTime: datetime.datetime
        """

        fig, mplSubplots = self.__buildFigureImpl(fromDateTime, toDateTime, postPlotFun=postPlotFun)
        fig.autofmt_xdate()
        plt.show()

    def savePlot(self, filename, dpi=None, format="png", fromDateTime=None, toDateTime=None):
        """
        Plot the strategy execution into a file. Must be called after running the strategy.

        :param filename: The filename.
        :param dpi: The resolution in dots per inch.
        :param format: The file extension.
        :param fromDateTime: An optional starting datetime.datetime. Everything before it won't get plotted.
        :type fromDateTime: datetime.datetime
        :param toDateTime: An optional ending datetime.datetime. Everything after it won't get plotted.
        :type toDateTime: datetime.datetime
        """

        fig, mplSubplots = self.__buildFigureImpl(fromDateTime=fromDateTime, toDateTime=toDateTime)
        fig.autofmt_xdate()
        fig.savefig(filename, dpi=dpi, bbox_inches="tight", format=format)

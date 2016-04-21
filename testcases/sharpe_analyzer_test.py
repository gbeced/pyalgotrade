# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

import datetime

import common
import strategy_test

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.broker import backtesting
from pyalgotrade import broker
from pyalgotrade import marketsession


class SharpeRatioTestCase(common.TestCase):
    def testDateTimeDiffs(self):
        # sharpe.days_traded
        self.assertEqual(sharpe.days_traded(datetime.datetime(2001, 1, 1), datetime.datetime(2001, 1, 2)), 2)
        self.assertEqual(sharpe.days_traded(datetime.datetime(2001, 1, 1), datetime.datetime(2001, 1, 2, 12)), 2)
        self.assertEqual(sharpe.days_traded(datetime.datetime(2001, 1, 1), datetime.datetime(2001, 1, 1, 12)), 1)
        self.assertEqual(sharpe.days_traded(datetime.datetime(2001, 1, 1), datetime.datetime(2001, 1, 1, 6)), 1)
        self.assertEqual(sharpe.days_traded(datetime.datetime(2001, 1, 1), datetime.datetime(2001, 1, 2, 6)), 2)

    def testNoTrades(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
        strat = strategy_test.TestStrategy(barFeed, 1000)
        stratAnalyzer = sharpe.SharpeRatio()
        strat.attachAnalyzer(stratAnalyzer)

        strat.run()
        self.assertTrue(strat.getBroker().getCash() == 1000)
        self.assertTrue(stratAnalyzer.getSharpeRatio(0.04, True) == 0)
        self.assertTrue(stratAnalyzer.getSharpeRatio(0) == 0)
        self.assertTrue(stratAnalyzer.getSharpeRatio(0, True) == 0)

    def __testIGE_BrokerImpl(self, quantity):
        initialCash = 42.09 * quantity
        # This testcase is based on an example from Ernie Chan's book:
        # 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)
        strat.setUseAdjustedValues(True)
        strat.setBrokerOrdersGTC(True)
        stratAnalyzer = sharpe.SharpeRatio()
        strat.attachAnalyzer(stratAnalyzer)

        # Disable volume checks to match book results.
        strat.getBroker().getFillStrategy().setVolumeLimit(None)

        # Manually place the order to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", quantity, True)  # Adj. Close: 42.09
        order.setGoodTillCanceled(True)
        strat.getBroker().submitOrder(order)
        strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", quantity, True)  # Adj. Close: 127.64
        strat.run()
        self.assertEqual(round(strat.getBroker().getCash(), 2), initialCash + (127.64 - 42.09) * quantity)
        self.assertEqual(strat.orderUpdatedCalls, 4)
        # The results are slightly different only because I'm taking into account the first bar as well.
        self.assertEqual(round(stratAnalyzer.getSharpeRatio(0.04, True), 4), 0.7889)
        self.assertEqual(round(stratAnalyzer.getSharpeRatio(0.04, False), 4), 0.0497)

    def testIGE_Broker(self):
        self.__testIGE_BrokerImpl(1)

    def testIGE_Broker2(self):
        self.__testIGE_BrokerImpl(2)

    def testIGE_BrokerWithCommission(self):
        commision = 0.5
        initialCash = 42.09 + commision
        # This testcase is based on an example from Ernie Chan's book:
        # 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)
        strat.getBroker().setCommission(backtesting.FixedPerTrade(commision))
        strat.setUseAdjustedValues(True)
        strat.setBrokerOrdersGTC(True)
        stratAnalyzer = sharpe.SharpeRatio()
        strat.attachAnalyzer(stratAnalyzer)

        # Disable volume checks to match book results.
        strat.getBroker().getFillStrategy().setVolumeLimit(None)

        # Manually place the order to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", 1, True)  # Adj. Close: 42.09
        order.setGoodTillCanceled(True)
        strat.getBroker().submitOrder(order)
        strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", 1, True)  # Adj. Close: 127.64

        strat.run()
        self.assertTrue(round(strat.getBroker().getCash(), 2) == initialCash + (127.64 - 42.09 - commision*2))
        self.assertEqual(strat.orderUpdatedCalls, 4)
        # The results are slightly different only because I'm taking into account the first bar as well,
        # and I'm also adding commissions.
        self.assertEqual(round(stratAnalyzer.getSharpeRatio(0.04, True), 6), 0.776443)

    def testIntraDay(self):
        barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, marketsession.USEquities.getTimezone())
        barFeed.setBarFilter(csvfeed.USEquitiesRTH())
        barFeed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
        strat = strategy_test.TestStrategy(barFeed, 1000)
        stratAnalyzer = sharpe.SharpeRatio(False)
        strat.attachAnalyzer(stratAnalyzer)
        strat.marketOrder("spy", 1)

        strat.run()

        tradingPeriods = 252*6.5*60
        manualAnnualized = sharpe.sharpe_ratio(stratAnalyzer.getReturns(), 0.04, tradingPeriods, True)
        manualNotAnnualized = sharpe.sharpe_ratio(stratAnalyzer.getReturns(), 0.04, tradingPeriods, False)
        analyzerAnnualized = stratAnalyzer.getSharpeRatio(0.04)
        analyzerNotAnnualized = stratAnalyzer.getSharpeRatio(0.04, False)

        self.assertEqual(round(analyzerAnnualized, 10), -1.1814830854)
        self.assertEqual(round(analyzerNotAnnualized, 10), -0.0037659686)
        # They should be similar, but not identical because the analyzer uses 365 days/year
        # when useDailyReturns is set to False.
        self.assertEqual(round(analyzerAnnualized, 1), round(manualAnnualized, 1))
        self.assertEqual(round(analyzerNotAnnualized, 3), round(manualNotAnnualized, 3))

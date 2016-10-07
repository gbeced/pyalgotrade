'''
There is implemented a twist of Mebane Faber Ivy League Tactical
Asset Allocation presented in [1], but adding cash contribution to the 
portfolio over the years to simulate real-life retail investor behavior.
Nonetheless, the yearly contribution is only used upon M.Faber rules while 
rolling out positions of the current portfolio.

[1] http://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461
A Quantitative Approach to Tactical Asset Allocation
Mebane T. Faber
Cambria Investment Management, February 1, 2013
The Journal of Wealth Management, Spring 2007 

'''

from pyalgotrade import strategy
from pyalgotrade.tools import yahoofinance
from pyalgotrade.technical import ma
import numpy as np

# portfolio analysis
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades
from pyalgotrade import plotter

IfMarketOrder = True # True -> self.marketOrder | False -> self.enterLong & self.__position[inst].exitMarket()

class Strategy1(strategy.BacktestingStrategy):
    def __init__(self, feed, cash, instruments):

        strategy.BacktestingStrategy.__init__(self, feed, cash)
        self.__instruments = instruments
        self.__position = {}
        self.__sma200 = {}
        self.month = 0
        self.year = 0
        self.TotalContribution = 0
        self.cash = cash

        for inst in instruments:
            price = feed[inst].getCloseDataSeries()
            self.__sma200[inst] = ma.SMA(price, 200)
            self.__position[inst] = 0

        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(False)

    def getSMA(self, ins, period):
        if period == 200:
            return self.__sma200[ins]

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL " +"Nb=" +str(execInfo.getQuantity()) +" "+ str(position.getEntryOrder().getInstrument()) +" at $%.2f" % (execInfo.getPrice()) 
        + " on " +str(execInfo.getDateTime()))
        self.__position[position.getEntryOrder().getInstrument()] = 0

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY " +"Nb=" +str(execInfo.getQuantity()) +" "+ str(position.getEntryOrder().getInstrument()) +" at " +str((execInfo.getPrice())) 
        + " on " +str(execInfo.getDateTime()))

    def onEnterCanceled(self, position):
        execInfo = position
        self.info("Enter Canceled for " + str(execInfo.getInstrument()) )
        self.__position[position.getEntryOrder().getInstrument()] = 0
    
    def onBars(self, bars):
        # contribute cash annually
        if self.year != bars.getDateTime().year:
            self.year = bars.getDateTime().year
            AnnualContribution = 10000
            self.TotalContribution +=  AnnualContribution
            self.getBroker().setCash(
                self.getBroker().getCash() + AnnualContribution)

# Mebane Faber IVY Portfolio
# http://www.investingdaily.com/18094/avoid-market-crashes-using-the-ivy-portfolio-market-timing-system/
# 1. wait for market close on last day of calendar month
    # - IF asset current market price > 10-month moving average, invest full allocation for next month
    # - IF asset current market price < 10-month MA, move to cash or intermediate-term US Treasury notes (5-10 yrs)
# 2. Ignore price fluctuation above or below the 10-month MA during month
# 3. All decision occur only once at the end of the month
#

        # trade once a month, on first day
        if self.month != bars.getDateTime().month:
            self.month = bars.getDateTime().month
            for inst in self.__instruments:

                    
                if self.__sma200[inst][-1] is not None:
                    
                    if bars[inst].getTypicalPrice()  > self.__sma200[inst][-1] and self.__position[inst] == 0:
                        # Portion of the portfolio attributed to that instrument: Equal weight between Instruments
                        Portion = 1/float(len(self.__instruments)) # equal weight amongst instruments (forcing one side float to overcome the issue with python v<3 that returns only integer values)
                        Liquidity =  0.9*self.getBroker().getCash() # 100% may create "Insufficient fund", thus default to 90%
                        NbUnits = np.floor(Liquidity * Portion /  bars[inst].getTypicalPrice())

                        if NbUnits > 0:
                            if not(IfMarketOrder):
                                self.__position[inst] = self.enterLong(inst, NbUnits, True)
                            else:
                                self.__position[inst] += NbUnits;                            
                                self.marketOrder(inst, self.__position[inst], True)
                                print(str(inst) + " Long Market Order in Year : " +str(bars.getDateTime().year) +" on Month " +str(bars.getDateTime().month) 
                                + " at Price: "+str(bars[inst].getTypicalPrice()) +" NbUnits = " +str(self.__position[inst]))
                        else: 
                            print("NbUnits is 0")

                    elif bars[inst].getTypicalPrice()  < self.__sma200[inst][-1] and self.__position[inst] > 0:
#                    using intermediate-term bonds instead of cash 
#                    to park the sale proceeds of asset classes that are currently under their moving average
                        if not(IfMarketOrder):
                            self.__position[inst].exitMarket()
                        else:
                            self.marketOrder(inst, -self.__position[inst], True)
                            print(str(inst) + " Exit-Long Market Order in Year : " +str(bars.getDateTime().year) +" on Month " +str(bars.getDateTime().month) 
                                + " at Price: "+str(bars[inst].getTypicalPrice()) +" NbUnits = " +str(self.__position[inst]))
                            self.__position[inst] = 0


def run_strategy(instruments, year, IfPlot):
    
    feed = yahoofinance.build_feed(instruments, int(year[0]), int(year[1]), "./DailyStockPrices")
    cash = 10000
    myStrategy = Strategy1(feed, cash, instruments)
    
    # Attach different analyzers to a strategy before executing it.
    retAnalyzer = returns.Returns()
    myStrategy.attachAnalyzer(retAnalyzer)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    myStrategy.attachAnalyzer(sharpeRatioAnalyzer)
    drawDownAnalyzer = drawdown.DrawDown()
    myStrategy.attachAnalyzer(drawDownAnalyzer)
    tradesAnalyzer = trades.Trades()
    myStrategy.attachAnalyzer(tradesAnalyzer)
    
    if IfPlot:
        #plots: Attach the plotter to the strategy.
        plt = plotter.StrategyPlotter(myStrategy)
        # Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
        for i in instruments:
            plt.getInstrumentSubplot(i).addDataSeries("SMA200", myStrategy.getSMA(i,200))
        # Plot the strategy returns at each bar.
#        plt.getOrCreateSubplot("returns").addDataSeries("Net return", retAnalyzer.getReturns())
#        plt.getOrCreateSubplot("returns").addDataSeries("Cum. return", retAnalyzer.getCumulativeReturns()) 
    
    # Run the strategy.
    myStrategy.run()
    # Plot the strategy.
    if IfPlot: plt.plot()
   
    print ("Final portfolio value: " +str( np.floor(myStrategy.getResult()) ) +" for a Total Contribution: "
        +str(myStrategy.TotalContribution) + " and Starting Capital of: " +str(myStrategy.cash) )
    Liquidity = myStrategy.TotalContribution+myStrategy.cash
    print ("Global ROI = " +str(100*(np.floor(myStrategy.getResult()-Liquidity)/Liquidity)) +"%")
    
    # portfolio analysis
    print "Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100)
    print "Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.05))
    print "Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100)
    print ("Longest drawdown duration: " +str(drawDownAnalyzer.getLongestDrawDownDuration()) +" days")


# http://mebfaber.com/timing-model/
# IVY: VNQ (ETF REIT) - Foreign stocks (VEU) - Commodities (DBC) - US stocks (VTI)
# iShares 1-3 Year Treasury Bond (SHY)- Bonds (BND) OR 10-yrs US Treas (IEF) 
# IVY 10 instruments:
    # bnd, dbc, gsG, rwx, tip, vb, veu, vnq, vti, vwo
year = ["2004","2013"]
instruments = ["AAPL", "MSFT"]
run_strategy(instruments, year, True)
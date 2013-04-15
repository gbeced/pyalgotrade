from pyalgotrade import plotter
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.stratanalyzer import returns
import smacross_strategy


# Load the yahoo feed from the CSV file
feed = yahoofeed.Feed()
feed.addBarsFromCSV("orcl", "orcl-2000.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = smacross_strategy.Strategy(feed, "orcl", 20)

# Attach a returns analyzers to the strategy.
returnsAnalyzer = returns.Returns()
myStrategy.attachAnalyzer(returnsAnalyzer)

# Attach the plotter to the strategy.
plt = plotter.StrategyPlotter(myStrategy)
# Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
plt.getInstrumentSubplot("orcl").addDataSeries("SMA", myStrategy.getSMA())
# Plot the strategy returns at each bar.
plt.getOrCreateSubplot("returns").addDataSeries("Net return", returnsAnalyzer.getReturns())
plt.getOrCreateSubplot("returns").addDataSeries("Cum. return", returnsAnalyzer.getCumulativeReturns())

# Run the strategy.
myStrategy.run()
print "Final portfolio value: $%.2f" % myStrategy.getResult()

# Plot the strategy.
plt.plot()


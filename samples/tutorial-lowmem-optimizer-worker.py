from pyalgotrade.optimizer import lowmemxmlrcpworker
import rsi2

if __name__ == "__main__":
    lowmemxmlrcpworker.run(rsi2.RSI2,
                           "localhost",
                           5000,
                           workerName="localworker")

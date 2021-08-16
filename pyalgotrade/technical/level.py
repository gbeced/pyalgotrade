# Use Level class to set a buy or sell level for an indicator, e.g.
# sell if RSI > 80

class LEVEL:
    
    def __init__(self, level):
        self.level = level
        
    def getSignal(self):
        return self.level
# Use Boolean class to set a boolean to compare to an indicator, e.g.
# sell if PSAR.reversal_toUptrend == True

class BOOLEAN:
    
    def __init__(self, boolean):
        self.boolean = boolean
        
    def getValue(self):
        return self.boolean
import enum
import sys

import pyalgotrade.fsm as fsm
import pyalgotrade.logger

logger = pyalgotrade.logger.getLogger('strategyfsm')


class SampleStrategyFSMState(enum.Enum):

    INIT = 1
    STATE1 = 2
    STATE2 = 3
    ERROR = 99


class SampleStrategyFSM(fsm.StrategyFSM):

    def __init__(self, barfeed, states):
        super(SampleStrategyFSM, self).__init__(barfeed, states)

    def print_bars(self, bars):
        for i in bars.getInstruments():
            logger.info('{} {} {}'.format(i, bars[i].getDateTime(), bars[i].getClose()))

    @fsm.state(SampleStrategyFSMState.INIT, True)
    def state_init(self, bars, states):
        # You are only supposed to save states in states variable
        # DO NOT save your local variable and it is not guaranteed to be supported later 
        logger.info('INIT')
        print(states.prev)
        states.prev = 'INIT'
        self.print_bars(bars)
        return SampleStrategyFSMState.STATE1
    
    @fsm.state(SampleStrategyFSMState.STATE1, False)
    def state_state1(self, bars, states):
        logger.info('STATE1')
        print(states.prev)
        states.prev = 'STATE1'
        self.print_bars(bars)
        return SampleStrategyFSMState.STATE2

    @fsm.state(SampleStrategyFSMState.STATE2, False)
    def state_state2(self, bars, states):
        logger.info('STATE2')
        print(states.prev)
        states.prev = 'STATE2'
        self.print_bars(bars)
        return SampleStrategyFSMState.ERROR
    
    @fsm.state(SampleStrategyFSMState.ERROR, False)
    def state_error(self, bars, states):
        logger.info('ERROR')
        sys.exit(0)

'''
Created on Jan 13, 2011

@author: alex
'''

import time as t
import numpy as np
from numpy.random import rand

class ExpDecay:
    def __init__(self, T0, Tend, maxTime, modulo=10 ): 
        self.maxTime = maxTime
        self.a = np.log(T0) - np.log( Tend )
        self.T0 = T0
        self.Tend = Tend
        self.modulo = modulo
        self.T = T0
        self.i = 0

    def getP( self, ev, evMaybe ):
        if self.i % self.modulo == 0: # do not update the temperature every iteration
            if self.i == 0: self.t0 = t.time() # first iteration
            self.r = (t.time()-self.t0)/self.maxTime # ratio of completion
            self.T = self.T0* np.exp( - self.a * self.r ) # exponential decay of temperature from T0 to Tend
            if self.r >= 1: return None # termination signal
        self.i += 1
        return np.exp( (ev - evMaybe) / self.T)


def anneal( obj, v2p, vMin = -np.inf, callback = None):

        rCount = 0 # rejection count
        aCount = 0 # acceptation count
        
        v = obj.value() # current value
        vBest = v # best value
        obj.flagBest()
        
        while True:
            
            vMaybe = obj.move()
            p = v2p.getP(v, vMaybe)
            if p is None:
#                print 'annealing has ended' 
                break # annealing has ended
            
            if rand() > p : # reject
                obj.revert()
                rCount += 1
            else:           # accept
                v = vMaybe
                if v < vBest: # found a better solution
                    vBest = v
                    obj.flagBest()
                aCount += 1
            
            if v <= vMin: 
#                print 'vMin reached'
                break # solution is good enough
            
            if callback is not None:
                callback( False, obj, vBest, v2p, rCount, aCount )

        callback( True, obj, vBest, v2p, rCount, aCount )

class Annealable:
    """interface for an object that can be annealed""" 
    def move(self):  pass # move to next state and return the new value
    def revert(self): pass # revert to the last state
    def flagBest(self): pass # remember this state
    def value(self): pass # returns the current value
        

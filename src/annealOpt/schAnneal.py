'''
Created on Jan 11, 2011

@author: alex

This is the module that is responsible for generating the schedule.

ScheduleLeague is the high level interface which receive information from the Config object.
It transforms the information in a more usable matrix where the team names and stadium names are removed.

ScheduleOpt is the object that implements Annealable. It must implement value(), move(), revert() and flagBest()
This object could be coded in c++ to obtain a huge gain in performance.

'''
#import cPickle
#import parseXls
#import model
import numpy as np
import anneal
#import mapUtil
from copy import deepcopy
import time as t 
from os import path
from util import writePkl, formatDelay, formatTime
ewLen = np.frompyfunc( len, 1,1) # an element-wise version of len  
    
t1 = t.time()
t0 = t.time()
 
cumDtSwap = 0
cumDtRest = 0

class SchAnneal( anneal.Annealable ):
    
    """
    Object that implements the schedule optimizer interface using simulated annealing
    scheduleMat = self.opt( config ):
    
    It also implements the annealable interface move(), revert(), flagBest()
    """
    
    def __init__( self, maxTime= 10*60, verbosity=3):
        self.T0 = 1e7
        self.Tend=0.1
        self.maxTime = maxTime
        self.verbosity=verbosity

    
    def setData(self, config ):
        
#        self.scheduleMat = config.scheduleMat

        self.penMat = config.getPenMat()
        self.fieldDate = config.getFieldDateMap()

        self.grpL = config.getGrpList()
        self.grpPenMat = config.getGrpPen()
        self.unifMagL, self.unifFieldGrpMap, self.pastUnifCount, _idMap = config.getUnifStruct()
 
        
        self.penDateFactor = config.penDateFactor
        self.currentPen = 0
        self.iter = 0
        self.moduloCheckIntegrity = 1000
        
        self._initTeamDateMap()
        self._initUnifCount()
        self.computePen()
        
    def findTRange(self):
        try:
            grpPen = np.array(zip( *self.grpL )[0])
        except IndexError:
            grpPen = np.array([0])
        structL = ( self.penMat, [self.penDateFactor], grpPen, grpPen/10. , self.unifMagL )
        
        aL = [] 
        for a in structL:
            a = np.asarray(a)
            if (a < 0).any() : 
                raise Exception( 'Negative penalty is invalid.')
            penL = a[ a != 0 * np.isfinite( a ) * -np.isnan( a ) ]
            if len(penL) > 0:
                aL.append(  penL  )
        
        penMin =  min([np.min( a ) for a in aL ] )
        penMax =  max([np.max( a ) for a in aL ] )
        
        return penMax*10., penMin/10.
        
    
    def _initTeamDateMap( self ):
        """Init the matrix that allows to list the game a team will play on the same date"""
        nTeam = self.penMat.shape[0]
        nDate = self.fieldDate.max()+1
        self.dateL = np.arange(nDate)

        teamDateMap = np.array([[ set() for _i in range(nTeam) ] for _j in range(nDate) ])
        
        for field, team1, team2 in self.scheduleMat:
            date = self.fieldDate[field]
            if team1 >= 0 : teamDateMap[ date, team1 ].add(field)
            if team2 >= 0 : teamDateMap[ date, team2 ].add(field)
        self.teamDateMap = teamDateMap 
        
        
        
        # make a map that tells which group a team belong to
        self.teamGrpMap = [ [] for _i in range(nTeam) ]
        for i,grp in enumerate(self.grpL):
            for team in grp[1]: self.teamGrpMap[team].append( i )
        self.teamGrpMap = np.array( self.teamGrpMap, dtype=np.object )
#        print self.teamGrpMap.shape
#        print self.teamGrpMap[[0,1]]
#        print self.teamGrpMap
    
    def _initUnifCount(self):
#        nTeam = self.penMat.shape[0]
#        unifCount_ = np.zeros( (len( self.unifMagL ), nTeam), dtype=np.int )
        
        unifCount = deepcopy( self.pastUnifCount )
        

        for field, team1, team2 in self.scheduleMat:
            if team1 >= 0:
                for idx in self.unifFieldGrpMap[ field ]:
                    unifCount[idx, team1] += 1
                    unifCount[idx, team2] += 1
        self.unifCount = unifCount
            
        
    
    def computePen( self ):
        """Compute the full penalty of the current schedule"""
        penL = [ self.penMat[ (team1,team2), field ].sum() 
            for field, team1, team2 in self.scheduleMat ] 
        self.penL = np.array(penL)
        self.currentPen = self.penL.sum()
        
        self.currentPen += self.concurrentPen()
        grpPen = self.grpPen(self.grpL, self.dateL)
        self.currentPen += grpPen
        self.currentPen += self.unifPen()
    
    def grpPen(self, grpL, dateL):
#        return 0
        pen = 0
        for date in dateL:
            for penRatio, teamL in grpL:
                
                # this represents all fields used by a group of team on a specific date.
                fieldL = list(set.union( *self.teamDateMap[date,teamL] )) 
                
                n = len(fieldL)
                

                if n == 2: # most of the cases
                    pen += penRatio* self.grpPenMat[ fieldL[0], fieldL[1] ]
                elif n>2:
                    for i in range( len(fieldL)):
                        for j in range(i): # i,j represent all unordered pairs of field
                            
                            pen += penRatio* self.grpPenMat[ fieldL[i], fieldL[j] ]
        
        return pen
              
    def unifPen( self, grpIdxL=None, teamIdxL=None ):
#        if teamIdxL is None:
        if True: # not slower, plus there seems to be a bug in the delta-update.
            return np.dot( self.unifMagL, 2** self.unifCount -1 ).sum()
        else:
            countL = self.unifCount[ grpIdxL, teamIdxL ]
            return  np.dot( self.unifMagL[ list(grpIdxL) ],  2**countL ).sum() # missing -1 ?
        
        
    
#    def concurrentPen_( self, countL ):
#        """Calculates the penalty associated with the number of concurrent game on the same date"""
#        countL = np.asarray( countL )
#        return ( (countL > 1) * (countL-1)  ).sum()  * self.penDateFactor
    
    def concurrentPen( self, idxL=None ):
        """
        Calculates the penalty associated with the number of concurrent game on the same date
        """
        
        if idxL is None: # all index
            countL = ewLen( self.teamDateMap ) 
        else:
            countL = ewLen( self.teamDateMap[ zip( *idxL ) ])
        return ( (countL > 1) * (countL-1)  ).sum()  * self.penDateFactor
    
    def checkIntegrity( self ):
        """
        Verifies the integrity of the structures.
        This makes sure that the differential updates equals the true values.
        """
        teamDateMap = deepcopy( self.teamDateMap )
        unifCount = deepcopy( self.unifCount )
        penL = deepcopy( self.penL )
        pen = self.currentPen
        
        self._initTeamDateMap()
        self._initUnifCount()
        self.computePen()
#        print unifCount
#        print teamDateMap
        
#        print unifCount.sum(), unifCount
        
        if self.verbosity > 0:
                       
            if not (penL == self.penL).all():
                print "checkIntegrety : incoherent penL"
            if not (teamDateMap == self.teamDateMap).all():
                print "checkIntegrety : incoherent teamDateMap"
            if not (unifCount == self.unifCount).all():
                print "checkIntegrety : incoherent unifCount %s"%(str(unifCount.shape))
                print unifCount
                print 'vs'
                print self.unifCount
                print 'diff'
                print self.unifCount - unifCount
            if abs(pen - self.currentPen) > 1e-3:
                print "checkIntegrety : incoherent penality, %.3g vs %.3g (diff = %.3g)"%(pen, self.currentPen, pen-self.currentPen)
            
    def getGrpIdxL(self, teamL ):
        """
        Returns each group (as a list of grpIdx) in self.grpL that 
        """
        grpIdxSet = set()
        [ grpIdxSet.update( grpIdxL ) for grpIdxL in self.teamGrpMap[ teamL ] ]
#        
#        if len(grpIdxSet) >0 : 
#            print teamL
#            print grpIdxSet
        
        return self.grpL[ list(grpIdxSet) ] # affected groups
    
    def value( self ):  return self.currentPen # Implements Annealable interface
    
    def move( self ):
        
        idx1, idx2 = np.random.randint(0, len(self.scheduleMat),2)
        self._swapField( idx1, idx2 )
        self.lastMove = (idx1, idx2)
        
        self.iter += 1
        if self.iter % self.moduloCheckIntegrity == 0: 
#            global cumDtRest, cumDtSwap
#            print "dtSwapRatio : %.3g"%(cumDtSwap/(cumDtRest+cumDtSwap) )
            self.checkIntegrity()
                
        return self.currentPen
        
    def revert(self):
        idx1, idx2 = self.lastMove
        self._swapField(idx1, idx2) 
        
    def _swapField( self, idxA, idxB ):
        """
        This function is responsible for swapping the fields and recompute the penalty of the new schedule. 
        To have a O(1) update complexity, the penalty is computed in a differential way. We first obtain which part of the schedule
        and related structures are affected. Then we substract the penalty related to the old assignation, we update the 
        structures and finally add the penalties related to the new assignation. 
        
        However, this approach is more complicated than I originally thought and might not be much faster than recomputing the 
        complete penalty each time. 
        """
        
#        global t0,t1, cumDtRest, cumDtSwap
#        t0 = t.time()
#        cumDtRest += t0-t1
        
        
        # fetching variables
        # ------------------

        if idxA == idxB : return # nothing change
        
        fieldA, team1A, team2A = self.scheduleMat[ idxA, : ]
        fieldB, team1B, team2B = self.scheduleMat[ idxB, : ]

#        nTeam = self.penMat.shape[0]
#        if (nTeam - 1) in (team1A, team1B, team2A, team2B ): print 'allo'
        
        if team1A == -1 and team1B == -1 : return # swapping between two unused fields

        dateA = self.fieldDate[fieldA]
        dateB = self.fieldDate[fieldB]

        grpIdxAL = tuple(self.unifFieldGrpMap[ fieldA ])
        grpIdxBL = tuple(self.unifFieldGrpMap[ fieldB ])
        nA = len(grpIdxAL)
        nB = len(grpIdxBL)

        # preparing index for teamDateMap and unifCount
        # --------------------------------------------
        
        if   team1A == -1: # fieldA is not used
            oldIdxL = ( (dateB,team1B,fieldB), (dateB,team2B,fieldB) )
            newIdxL = ( (dateA,team1B,fieldA), (dateA,team2B,fieldA) )
            oldUnifIdxL = ( grpIdxBL*2 , (team1B,)*nB + (team2B,)*nB ) 
            newUnifIdxL = ( grpIdxAL*2 , (team1B,)*nA + (team2B,)*nA )
            grpL = self.getGrpIdxL([team1B, team2B] )
            
        elif team1B == -1: # fieldB is not used
            oldIdxL = ( (dateA,team1A,fieldA), (dateA,team2A,fieldA) )
            newIdxL = ( (dateB,team1A,fieldB), (dateB,team2A,fieldB) )
            oldUnifIdxL = ( grpIdxAL*2 , (team1A,)*nA + (team2A,)*nA ) 
            newUnifIdxL = ( grpIdxBL*2 , (team1A,)*nB + (team2A,)*nB )
            grpL = self.getGrpIdxL( [team1A, team2A])
        else:
            oldIdxL = ( (dateA,team1A,fieldA), (dateA,team2A,fieldA), (dateB,team1B,fieldB), (dateB,team2B,fieldB) )
            newIdxL = ( (dateB,team1A,fieldB), (dateB,team2A,fieldB), (dateA,team1B,fieldA), (dateA,team2B,fieldA) )
            oldUnifIdxL = ( grpIdxAL*2 + grpIdxBL*2 , (team1A,)*nA + (team2A,)*nA +  (team1B,)*nB + (team2B,)*nB ) 
            newUnifIdxL = ( grpIdxAL*2 + grpIdxBL*2 , (team1B,)*nA + (team2B,)*nA +  (team1A,)*nB + (team2A,)*nB )
            grpL = self.getGrpIdxL([team1A, team2A, team1B, team2B ])

#        if len(grpL)>0 : print grpL
#        grpL = self.grpL
    
        tmp = zip( * (oldIdxL + newIdxL))
        idxSet = set( zip(tmp[0], tmp[1] )) # the set of all affected cells in teamDateMap
        if dateA == dateB: dateL = (dateA,)
        else:              dateL = (dateA,dateB)
        
#        assert (np.asarray(newUnifIdxL) >= 0 ).all()
#        assert (np.asarray(oldUnifIdxL) >= 0 ).all()
        
        # removing penalty related to old assignation
        # -------------------------------------------
        
        self.currentPen -= self.penL[ idxA ]
        self.currentPen -= self.penL[ idxB ]
        self.currentPen -= self.concurrentPen( idxSet ) 
        
        self.currentPen -= self.grpPen(grpL, dateL)
        
        self.currentPen -= self.unifPen( *oldUnifIdxL )

        # updating structures 
        # -------------------
        
        # assigning new fields
        self.scheduleMat[ idxB, 0 ] = fieldA
        self.scheduleMat[ idxA, 0 ] = fieldB

        # updating penalties list
        self.penL[idxA] = self.penMat[ (team1A, team2A), fieldB ].sum() 
        self.penL[idxB] = self.penMat[ (team1B, team2B), fieldA ].sum() 

        # update teamDateMap
        for date, team, field in oldIdxL:
            self.teamDateMap[date, team].remove( field )
        for date, team, field in newIdxL:
            self.teamDateMap[date, team].add( field )


        # update unifCount
        self.unifCount[ oldUnifIdxL ] -=1
        self.unifCount[ newUnifIdxL ] +=1


        # adding new penalties
        # -------------------- 
        
        self.currentPen += self.penL[idxA]
        self.currentPen += self.penL[idxB]
        self.currentPen += self.concurrentPen( idxSet ) 
        self.currentPen += self.grpPen(grpL, dateL)
        self.currentPen += self.unifPen( *newUnifIdxL )


#        t1 = t.time()
#        cumDtSwap += t1-t0
        

    def flagBest(self):
        self.bestSch = deepcopy( self.scheduleMat )


    def opt(self, config, schMat=None):
        if schMat is None:
            schMat = config.randomScheduleMat()
        self.scheduleMat = schMat
        self.setData(config)
        T0, Tend = self.findTRange()
        decay = anneal.ExpDecay( T0, Tend, self.maxTime)
        anneal.anneal(self, decay, 0,callback=Callback(config,self.verbosity))
        return config.getScheduleFromMat( self.bestSch )
    

#def fieldByDate( fieldL ):
#    """rearrange field by date and sort the date"""
#    fieldLD = {}
#    
#    for field in fieldL:
#        try:              fieldLD[field.date].append( field )
#        except KeyError : fieldLD[field.date] = [field]
#            
#    dateL = fieldLD.keys()
#    dateL.sort()
#    
##    for key, val in fieldLD.iteritems():
##        print key, val
#    
#    return [ fieldLD[date] for date in dateL ], dateL
    
    
    


class OptState():
    
    def __init__(self, finished, vBest, v2p, startTime, speed):
        self.vBest = vBest
        self.speed = speed
        self.finished = finished
        self.v2p = v2p
        self.startTime = startTime
    
    def __html__(self):
        maxTime = self.v2p.maxTime
        endTime = maxTime + self.startTime
        elapsedTime = t.time() - self.startTime
        timeLeft = endTime - t.time()
        percentDone = 100.*(maxTime-timeLeft)/maxTime 
        strL = []
        strL.append( "started at %s for %s, ending at %s"%(
            formatTime( self.startTime ), formatDelay( maxTime ), formatTime( endTime ) ) )
        if self.finished:
            strL.append( 'Optimization finished.')
            strL.append( '%d schedules explored.'%self.v2p.i)
        else:
            barStr = """<table width="50%%" height="10" cellspacing="0"><tr><td width="%f%%" bgcolor="green"></td><td bgcolor="#AAAAAA"></td></tr> </table>"""
#            strL.append("Shaking it really hard baby !!!")
            strL.append( "%s left (%d%% done and %d schedules explored)"%( formatDelay( timeLeft ), percentDone, self.v2p.i) )
            strL.append(  barStr%( max(1,percentDone) )  )
#            strL.append( "Current speed : %.1f schedule / s "% (self.speed) )
            strL.append( 'average speed : %.1f schedule / s'%(float(self.v2p.i) / elapsedTime ) )
            strL.append( 'Temperature %.3g (%.3g ... %.3g)'%(self.v2p.T, self.v2p.T0, self.v2p.Tend ) )
        return "<br/>\n".join( strL )

class Callback:

    def __init__(self, config, verbosity, moduloPrint=1000, moduloAnalyse=float('nan')):
        self.t = t.time()
        self.verbosity = verbosity
        self.startTime= t.time()
        self.moduloPrint = moduloPrint
        self.moduloAnalyse = moduloAnalyse
        self.config = config
        self.pklPath = path.join( config.workFolder, 'sch.pkl' )
    
    
    def __call__(self, finished, annealable, vBest, v2p, rCount, aCount ):
        if (v2p.i % self.moduloPrint == 0) or finished:
            now= t.time()
            speed = self.moduloPrint / (now-self.t)
            if self.verbosity > 1:
                print 'i=%d, ratio : %.3f, bestVal :%.3g, T=%.3g, dt=%.3fs'%(v2p.i,v2p.r,vBest,v2p.T, now-self.t)
            self.t = now
            matchL = self.config.getScheduleFromMat( annealable.bestSch )
            
            optState = OptState( finished, vBest, v2p, self.startTime, speed )
            writePkl( (self.config, matchL, optState), self.pklPath, lock_block=True)
            
#        if v2p.i % self.moduloAnalyse == 0:
#            matchL = self.config.getScheduleFromMat( annealable.bestSch )
#            doc = HtmlDoc( HtmlAnalysis( self.config, matchL) )
#            doc.head.add(HtmlRefresh())
#            doc.write('example/analysis.html')


#def benchBasicSchedule():
#    import cProfile
#    import pstats
#    cProfile.run('testBasicSchedule()','bench')
#    p = pstats.Stats('bench')
#    
#    p.sort_stats('time')
#    p.print_stats()

#if __name__ == "__main__":
##    testBasicSchedule()
#    testScheduleLeague()
#            










#class BiMap:
#    
#    def __init__(self, it):
#        itemL = list(it)
#        itemL.sort()
#        self.key2idx = dict(  zip( itemL, range(len(itemL)) )  )
#        self.idx2key = itemL 
#        self._len = len( itemL )
#        
#    def __len__(self): return self._len


    

#
#
#class ScheduleOpt:
#    
#    def __init__( self, config, opt=None ):
#        self.config = config
#        if opt is None:
#            opt = SchAnneal()
#        self.opt = opt
#        self.league = config.league
#        self.fieldL = makeMap(config.fieldL)
#        self.restrD = config.restrD
#        self.unifL = config.unifL
#        self.teamL = self.league.getTeamL()
#        self._buildGrpList(config.grpL)
        
#        if opt is None:
#            self.opt = 
        
#        noTeam = model.Team( '[no-body]' ) # indicates that there no teams on that field
#        noTeam.idx = len( self.teamL )
#        self.teamL.append(noTeam )
#        self._initSruct()
#    
#    def _buildPenMat(self):
#        penMat = np.zeros( ( len(self.teamL)+1, len( self.fieldL ) ) )
#        # add one more team so that penMat[ -1, : ] = 0. This is useful since team -1 represents a free field.
#        for team in self.teamL:
#            for field in self.fieldL:
#                pen = 0
#                for restr in self.restrD.get( (team, field.date ) , [] ):
#                    pen += restr.getPen(field)
#                penMat[ team.idx, field.idx ] = pen
#
#
#        self.penMat = penMat
#
#    def _buildGrpList(self,grpL):
#        self.grpL = []
#        for pen, teamL in grpL:
#            self.grpL.append( ( pen, [team.idx for team in teamL ]))
#        self.grpL = np.array( self.grpL, dtype=np.object )  # transform into numpy array so we can batch-index elements.
#        
#    
#    def _buildGrpPen(self):
#        """
#        Build a penalty matrix for playing two games on the same day.
#        The result is a symmetric field x field matrix.
#        When it is not playable (big time overlap), penalty is 1.
#        when it is playable but with a gap of 5h or on different stadium, the penalty is 0.3
#        When it is in the same stadium, the penalty range from 0 to 0.3 depending on the time gap 
#        """
#        n = len(self.fieldL)
#        penMat = np.zeros( (n,n) )
#
#        for i in range(n):
#            penMat[i,i] = 1.
#            for j in range(i):
#                fieldA = self.fieldL[i]
#                fieldB = self.fieldL[j]
#                
#                if fieldA.date != fieldB.date : continue # not the same day -> pen = 0
#        
#                if fieldA.time > fieldB.time : # makes sure that fieldA starts before FieldB
#                    fieldA, fieldB = fieldB, fieldA
#                
#                
#                dt = fieldB.time - fieldA.endTime # time gap
#                
#                if fieldA.stadium != fieldB.stadium :
#                    if dt >= 60 :  pen = 0.3  # playable but not cool !
#                    else: pen = 1. # not playable
#                else:
#                    if   dt < -15 : pen = 1. # not playable
#                    elif dt < 0 : pen = 0.5 # 15 minutes overlap ... not so bad :p
#                    elif dt > 60.*5. : pen = 0.3 # playable but long delay
#                    else : pen = 0.3 * dt/(60.*5.) # penalty proportional to delay
#                        
#                penMat[i,j] = pen
#                penMat[j,i] = pen
#                
#        self.grpPenMat = penMat
#            
#    
#    def _buildUnifStruct(self):
#        
#        idSet = set( [ el[0] for el in self.unifL ] )
#        idMap = dict( zip( list(idSet), range(len(idSet)) ) )
#        
#        self.unifMagL = [0.]* len(idSet)
#        for id_, mag, _restr in self.unifL:
##            print _restr
##            print 
#            self.unifMagL[ idMap[id_] ] = mag
#        
#        self.unifFieldGrpMap = []
#        for field in self.fieldL:
#            grpSet = set()
#            for id_, mag, restr in self.unifL:
##                print field.time, restr.timeMin, restr.timeMax, restr.stadiumS, restr.fNameS
#                if restr.isActive(field):
##                    print 'active'
#                    grpSet.add( idMap[id_] )
#            self.unifFieldGrpMap.append( list(grpSet) )
##        print self.unifFieldGrpMap
#        
#            
#
#    def _initSruct( self ):
#        self.fieldDateMap = np.array([ field.date.idx for field in self.fieldL ])
#        self._buildPenMat()
#        self._buildGrpPen()
#        self._buildUnifStruct()
#        self.randomSchedule()
#        
        

        
    
    
#    def opt(self, T0 = 1e8, Tend=0.1, maxTime=15*60 ):
#        schOpt = SchAnneal( self.scheduleMat, self.penMat, self.fieldDateMap, 
#            self.grpPenMat, self.grpL, self.unifMagL, self.unifFieldGrpMap)
#        decay = anneal.ExpDecay( T0, Tend, maxTime)
#        anneal.anneal(schOpt, decay, 0,callback=Callback())
#        self.scheduleMat = schOpt.bestSch
#        
#    
#    def __str__(self):
#        strL = []
#        for fieldIdx, team1Idx, team2Idx in self.scheduleMat:
#            if team1Idx == -1: continue
#            team1 = self.teamL[ team1Idx ]
#            team2 = self.teamL[ team2Idx ]
#            field = self.fieldL[ fieldIdx ]
#            strL.append( '[%s] vs [%s] on %s'%( team1.name, team2.name, field.name  ) )
#        return '\n'.join(strL)
#    
#    def getSchedule(self):
#        matchL = []
#        for fieldIdx, team1Idx, team2Idx in self.scheduleMat:
#            if team1Idx == -1: continue
#            match = model.Match( self.teamL[ team1Idx ], self.teamL[ team2Idx ] )
#            match.field = self.fieldL[ fieldIdx ]
#            matchL.append( match )
#        
#        return Schedule( matchL )
#     
    
#    def __str__(self):
#        pass











#
#def testScheduleLeague():
#    f = open("leagues.pkl")
#    leagueL = cPickle.load(f)
#    league = leagueL[1]
#    config = parseXls.Config('config.xls',league)
#
#    sch = ScheduleLeague( league, config.fieldL, config.restrD, config.teamGrpD.values() )
#    sch.opt()
#    sch = sch.getSchedule()
#    
#    
#    print '============================='
#    print sch
#    print '============================='    
##
#def testBasicSchedule():
#    f = open("leagues.pkl")
#    leagueL = cPickle.load(f)
#    league = leagueL[1]
#    config = parseXls.Config('config.xls',league)
#    fieldLL, dateL = fieldByDate(config.fieldL) 
#
#    schedule0 = genBasicSchedule(league.divisionL, fieldLL)
#
#    matchL_ = []
#    for matchL in schedule0:
#        matchL_ += matchL
#
#    sch = ScheduleDiv(matchL_, config.restrD, config.dateSrv.values(), config.teamSrv.values())
#
#    decay = anneal.ExpDecay(10000,0.1,10)
#    anneal.anneal(sch, decay, -1,callback=callback)
#    print '============================='
#    print sch
#    print '============================='                
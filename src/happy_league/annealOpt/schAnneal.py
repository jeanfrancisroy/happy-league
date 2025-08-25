"""Created on Jan 11, 2011

@author: alex

This is the module that is responsible for generating the schedule.

ScheduleLeague is the high level interface which receives information from the Config object.
It transforms the information in a more usable matrix where the team names and stadium names are removed.

ScheduleOpt is the object that implements Annealable. It must implement value(), move(), revert() and flagBest()
This object could be coded in c++ to obtain a huge gain in performance.

"""
import numpy as np
from . import anneal
from copy import deepcopy
import time as t
from os import path
from happy_league.util import write_pickle, formatDelay, formatTime
ewLen = np.frompyfunc(len, 1, 1)  # an element-wise version of len

t1 = t.time()
t0 = t.time()

cumDtSwap = 0
cumDtRest = 0


class SchAnneal(anneal.Annealable):
    """
    Object that implements the schedule optimizer interface using simulated annealing
    scheduleMat = self.opt( config ):

    It also implements the annealable interface move(), revert(), flagBest()

    """
    def __init__(self, maxTime=10*60, verbosity=3):
        self.T0 = 1e7
        self.Tend = 0.1
        self.maxTime = maxTime
        self.verbosity = verbosity

    def setData(self, config):
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
            grpPen = np.array(list(zip(*self.grpL))[0])
        except IndexError:
            grpPen = np.array([0])
        structL = (self.penMat, [self.penDateFactor], grpPen, grpPen/10., self.unifMagL)

        aL = []
        for a in structL:
            a = np.asarray(a)
            if (a < 0).any():
                raise Exception('Negative penalty is invalid.')
            penL = a[(a != 0) & np.isfinite(a)]
            if len(penL) > 0:
                aL.append(penL)

        penMin = min([np.min(a) for a in aL])
        penMax = max([np.max(a) for a in aL])

        return penMax*10., penMin/10.

    def _initTeamDateMap(self):
        """Init the matrix that allows to list the game a team will play on the same date"""
        nTeam = self.penMat.shape[0]
        nDate = self.fieldDate.max()+1
        self.dateL = np.arange(nDate)

        teamDateMap = np.array([[set() for _i in range(nTeam)] for _j in range(nDate)])

        for field, team1, team2 in self.scheduleMat:
            date = self.fieldDate[field]
            if team1 >= 0:
                teamDateMap[date, team1].add(field)
            if team2 >= 0:
                teamDateMap[date, team2].add(field)
        self.teamDateMap = teamDateMap

        # make a map that tells which group a team belong to
        self.teamGrpMap = [[] for _i in range(nTeam)]
        for i, grp in enumerate(self.grpL):
            for team in grp[1]:
                self.teamGrpMap[team].append(i)
        self.teamGrpMap = np.array(self.teamGrpMap, dtype=object)

    def _initUnifCount(self):
        unifCount = deepcopy(self.pastUnifCount)

        for field, team1, team2 in self.scheduleMat:
            if team1 >= 0:
                for idx in self.unifFieldGrpMap[field]:
                    unifCount[idx, team1] += 1
                    unifCount[idx, team2] += 1
        self.unifCount = unifCount

    def computePen(self):
        """Compute the full penalty of the current schedule"""
        penL = [self.penMat[(team1, team2), field].sum() for field, team1, team2 in self.scheduleMat]
        self.penL = np.array(penL)
        self.currentPen = self.penL.sum()
        self.currentPen += self.concurrentPen()
        grpPen = self.grpPen(self.grpL, self.dateL)
        self.currentPen += grpPen
        self.currentPen += self.unifPen()

    def grpPen(self, grpL, dateL):
        pen = 0
        for date in dateL:
            for penRatio, teamL in grpL:

                # this represents all fields used by a group of team on a specific date.
                fieldL = list(set.union(*self.teamDateMap[date, teamL]))

                n = len(fieldL)

                if n == 2:  # most of the cases
                    pen += penRatio * self.grpPenMat[fieldL[0], fieldL[1]]
                elif n > 2:
                    for i in range(len(fieldL)):
                        for j in range(i):  # i,j represent all unordered pairs of field
                            pen += penRatio * self.grpPenMat[fieldL[i], fieldL[j]]

        return pen

    def unifPen(self, grpIdxL=None, teamIdxL=None):
        # TODO: Is there a bug here?
        # if teamIdxL is None:
        if True:  # not slower, plus there seems to be a bug in the delta-update.
            return np.dot(self.unifMagL, 2 ** self.unifCount - 1).sum()
        else:
            countL = self.unifCount[grpIdxL, teamIdxL]
            return np.dot(self.unifMagL[list(grpIdxL)],  2**countL).sum()  # missing -1 ?

    def concurrentPen(self, idxL=None):
        """Calculates the penalty associated with the number of concurrent game on the same date

        """
        if idxL is None:  # all index
            countL = ewLen(self.teamDateMap)
        else:
            rows, cols = zip(*sorted(idxL))
            rows = np.array(rows)
            cols = np.array(cols)

            countL = ewLen(self.teamDateMap[rows, cols])
        return ((countL > 1) * (countL-1)).sum() * self.penDateFactor

    def checkIntegrity(self):
        """Verifies the integrity of the structures.
        This makes sure that the differential updates equals the true values.

        """
        teamDateMap = deepcopy(self.teamDateMap)
        unifCount = deepcopy(self.unifCount)
        penL = deepcopy(self.penL)
        pen = self.currentPen

        self._initTeamDateMap()
        self._initUnifCount()
        self.computePen()

        if self.verbosity > 0:
            if not (penL == self.penL).all():
                print("checkIntegrety : incoherent penL")
            if not (teamDateMap == self.teamDateMap).all():
                print("checkIntegrety : incoherent teamDateMap")
            if not (unifCount == self.unifCount).all():
                print("checkIntegrety : incoherent unifCount %s" % (str(unifCount.shape)))
                print(unifCount)
                print('vs')
                print(self.unifCount)
                print('diff')
                print(self.unifCount - unifCount)
            if abs(pen - self.currentPen) > 1e-3:
                print("checkIntegrety : incoherent penality, %.3g vs %.3g (diff = %.3g)" % (pen, self.currentPen, pen-self.currentPen))

    def getGrpIdxL(self, teamL):
        """
        Returns each group (as a list of grpIdx) in self.grpL that
        """
        grpIdxSet = set()

        for grpIdxL in self.teamGrpMap[teamL]:
            grpIdxSet.update(grpIdxL)

        return self.grpL[list(grpIdxSet)]  # affected groups

    def value(self):
        return self.currentPen  # Implements Annealable interface

    def move(self):
        idx1, idx2 = np.random.randint(0, len(self.scheduleMat), 2)
        self._swapField(idx1, idx2)
        self.lastMove = (idx1, idx2)

        self.iter += 1
        if self.iter % self.moduloCheckIntegrity == 0:
            self.checkIntegrity()

        return self.currentPen

    def revert(self):
        idx1, idx2 = self.lastMove
        self._swapField(idx1, idx2)

    def _swapField(self, idxA, idxB):
        """
        This function is responsible for swapping the fields and recompute the penalty of the new schedule.
        To have a O(1) update complexity, the penalty is computed in a differential way. We first obtain which part of the schedule
        and related structures are affected. Then we substract the penalty related to the old assignation, we update the
        structures and finally add the penalties related to the new assignation.

        However, this approach is more complicated than I originally thought and might not be much faster than recomputing the
        complete penalty each time.
        """

        # fetching variables
        # ------------------
        if idxA == idxB:
            return  # nothing changes

        fieldA, team1A, team2A = self.scheduleMat[idxA, :]
        fieldB, team1B, team2B = self.scheduleMat[idxB, :]

        if team1A == -1 and team1B == -1:
            return  # swapping between two unused fields

        dateA = self.fieldDate[fieldA]
        dateB = self.fieldDate[fieldB]

        grpIdxAL = tuple(self.unifFieldGrpMap[fieldA])
        grpIdxBL = tuple(self.unifFieldGrpMap[fieldB])
        nA = len(grpIdxAL)
        nB = len(grpIdxBL)

        # preparing index for teamDateMap and unifCount
        # --------------------------------------------

        if team1A == -1:  # fieldA is not used
            oldIdxL = ((dateB, team1B, fieldB), (dateB, team2B, fieldB))
            newIdxL = ((dateA, team1B, fieldA), (dateA, team2B, fieldA))
            oldUnifIdxL = (grpIdxBL*2, (team1B,)*nB + (team2B,)*nB)
            newUnifIdxL = (grpIdxAL*2, (team1B,)*nA + (team2B,)*nA)
            grpL = self.getGrpIdxL([team1B, team2B])

        elif team1B == -1:  # fieldB is not used
            oldIdxL = ((dateA, team1A, fieldA), (dateA, team2A, fieldA))
            newIdxL = ((dateB, team1A, fieldB), (dateB, team2A, fieldB))
            oldUnifIdxL = (grpIdxAL*2, (team1A,)*nA + (team2A,)*nA)
            newUnifIdxL = (grpIdxBL*2, (team1A,)*nB + (team2A,)*nB)
            grpL = self.getGrpIdxL([team1A, team2A])
        else:
            oldIdxL = ((dateA, team1A, fieldA), (dateA, team2A, fieldA), (dateB, team1B, fieldB), (dateB, team2B, fieldB))
            newIdxL = ((dateB, team1A, fieldB), (dateB, team2A, fieldB), (dateA, team1B, fieldA), (dateA, team2B, fieldA))
            oldUnifIdxL = (grpIdxAL*2 + grpIdxBL*2, (team1A,)*nA + (team2A,)*nA + (team1B,)*nB + (team2B,)*nB)
            newUnifIdxL = (grpIdxAL*2 + grpIdxBL*2, (team1B,)*nA + (team2B,)*nA + (team1A,)*nB + (team2A,)*nB)
            grpL = self.getGrpIdxL([team1A, team2A, team1B, team2B])

        tmp = list(zip(* (oldIdxL + newIdxL)))
        idxSet = set(zip(tmp[0], tmp[1]))  # the set of all affected cells in teamDateMap
        if dateA == dateB:
            dateL = (dateA,)
        else:
            dateL = (dateA, dateB)

        # removing penalty related to old assignation
        # -------------------------------------------

        self.currentPen -= self.penL[idxA]
        self.currentPen -= self.penL[idxB]
        self.currentPen -= self.concurrentPen(idxSet)
        self.currentPen -= self.grpPen(grpL, dateL)
        self.currentPen -= self.unifPen(*oldUnifIdxL)

        # updating structures
        # -------------------

        # assigning new fields
        self.scheduleMat[idxB, 0] = fieldA
        self.scheduleMat[idxA, 0] = fieldB

        # updating penalties list
        self.penL[idxA] = self.penMat[(team1A, team2A), fieldB].sum()
        self.penL[idxB] = self.penMat[(team1B, team2B), fieldA].sum()

        # update teamDateMap
        for date, team, field in oldIdxL:
            self.teamDateMap[date, team].remove(field)
        for date, team, field in newIdxL:
            self.teamDateMap[date, team].add(field)

        # update unifCount
        self.unifCount[oldUnifIdxL] -= 1
        self.unifCount[newUnifIdxL] += 1

        # adding new penalties
        # --------------------
        self.currentPen += self.penL[idxA]
        self.currentPen += self.penL[idxB]
        self.currentPen += self.concurrentPen(idxSet)
        self.currentPen += self.grpPen(grpL, dateL)
        self.currentPen += self.unifPen(*newUnifIdxL)

    def flagBest(self):
        self.bestSch = deepcopy(self.scheduleMat)

    def opt(self, config, schMat=None):
        if schMat is None:
            schMat = config.randomScheduleMat()
        self.scheduleMat = schMat
        self.setData(config)
        T0, Tend = self.findTRange()
        decay = anneal.ExpDecay(T0, Tend, self.maxTime)
        anneal.anneal(self, decay, 0, callback=Callback(config, self.verbosity))
        return config.getScheduleFromMat(self.bestSch)


class OptState:
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
        self.startTime = t.time()
        self.moduloPrint = moduloPrint
        self.moduloAnalyse = moduloAnalyse
        self.config = config
        self.pklPath = path.join(config.workFolder, 'sch.pkl')

    def __call__(self, finished, annealable, vBest, v2p, rCount, aCount):
        if (v2p.i % self.moduloPrint == 0) or finished:
            now = t.time()
            speed = self.moduloPrint / (now-self.t)
            if self.verbosity > 1:
                print('i=%d, ratio : %.3f, bestVal :%.3g, T=%.3g, dt=%.3fs' % (v2p.i, v2p.r, vBest, v2p.T, now-self.t))
            self.t = now
            matchL = self.config.getScheduleFromMat(annealable.bestSch)

            optState = OptState(finished, vBest, v2p, self.startTime, speed)
            write_pickle((self.config, matchL, optState), self.pklPath)

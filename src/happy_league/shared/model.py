"""
Created on Jan 12, 2011

@author: alex

This is the model of this schedule generator.
Every module depends on this one. Therefore, it must be as stable as possible.

Most objects speaks for themselves

"""
import numpy as np

from happy_league.shared.util import unparseTime


def teamSortKey(x):
    return x.rank


class Field:
    def __init__(self, stadium, name, time, date, duration=60.):
        self.stadium = stadium
        self.name = name
        self.time = time  # in minutes
        self.date = date
        self.endTime = time + duration

    def key(self):
        return (self.stadium, self.name, self.time, self.date.key())

    def __str__(self):
        h, m = unparseTime(self.time)
        return '%s-%s, %s %d:%02d' % (self.stadium, self.name, str(self.date), h, m)

    def __repr__(self):
        return str(self)


class Date:
    def __init__(self, year, month, day):
        self.date = (year, month, day)

    def key(self):
        return self.date

    def __hash__(self):
        return hash(self.date)

    def __str__(self):
        return "%d/%d/%d" % self.date

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        year, month, day = self.date
        other_year, other_month, other_day = other.date
        return year == other_year and month == other_month and day == other_day

    def __lt__(self, other):
        year, month, day = self.date
        other_year, other_month, other_day = other.date

        if year == other_year:
            if month == other_month:
                return day < other_day
            return month < other_month
        return year < other_year


class Match:
    def __init__(self, team1, team2):
        self.field = None
        self.team1 = team1
        self.team2 = team2
        self.pen = 0  # penality of having those teams on this field

    def updatePen(self, restrMat):
        pen = 0
        dateIdx = self.field.date.idx
        for restr in restrMat[self.team1.idx, dateIdx]:
            pen += restr.getPen(self.field)
        for restr in restrMat[self.team2.idx, dateIdx]:
            pen += restr.getPen(self.field)

        self.pen = pen

    def key(self):
        return (self.team1.key(), self.team2.key(), self.field.key())

    def __str__(self):
        return '%s vs %s on %s' % (self.team1, self.team2, self.field)


class League:
    def __init__(self, divisionL):
        self.name = ""
        self.divisionL = divisionL
        self.divisionL.sort(key=teamSortKey)

    def key(self):
        return self.name.lower()

    def getMatchL(self, nMatchPerTeam):
        matchL = []
        for division in self.divisionL:
            matchL += division.getMatchL(nMatchPerTeam)

        return matchL

    def getTeamL(self):
        teamL = []
        for division in self.divisionL:
            teamL += division.teamL
        return orderList(teamL)

    def __str__(self):
        strL = []
        for div in self.divisionL:
            strL.append(str(div))
        return '\n'.join(strL)


def roundRobin(nTeam, nMatch=None):
    if nMatch is None:
        nMatch = nTeam-1
    if nTeam % 2 == 0:
        idxL = np.arange(0, nTeam-1)
    else:
        idxL = np.arange(-1, nTeam-1)

    matchL = []
    i = 0
    while True:
        idxL_ = [nTeam-1] + list(np.roll(idxL, i))
        for j in range(len(idxL_)//2):
            match = (idxL_[j], idxL_[-j-1])
            if match[0] >= 0 and match[1] >= 0:
                matchL.append(match)
            if countMatch(nTeam, nMatch, matchL):
                return matchL
        i += 1
    return matchL


def roundRobinPair(nTeam1, nTeam2, nMatch):
    if nTeam1 > nTeam2:
        nTeam1, nTeam2 = nTeam2, nTeam1
        swap = True
    else:
        swap = False

    idx1L = np.arange(nTeam1)
    idx2L = np.arange(nTeam2)
    matchL = []
    for i in range(nMatch):
        idx2L_ = np.roll(idx2L, i)[:nTeam1]
        if not swap:
            matchL += zip(idx1L, idx2L_)
        else:
            matchL += zip(idx2L_, idx1L)

    return matchL


def countMatch(nTeam, nMatch, matchL):
    countL = np.zeros(nTeam)
    for t1, t2 in matchL:
        countL[t1] += 1
        countL[t2] += 1

    return all([count >= nMatch for count in countL])


def verifyMatchL(nTeam, nMatch, matchL):
    pass


def testRoundRobin():
    nTeam = 5
    nMatch = 7
    count = np.zeros(nTeam)
    matchCount = np.zeros((nTeam, nTeam))

    for t1, t2 in roundRobin(nTeam, nMatch):
        count[t1] += 1
        count[t2] += 1
        if t1 > t2:
            t1, t2 = t2, t1
        matchCount[t1, t2] += 1
        print(t1, t2)
    print(count)
    print(matchCount)


def testRoundRobinPair():
    nTeam1 = 3
    nTeam2 = 2
    nMatch = 4
    matchCount = np.zeros((nTeam1, nTeam2))

    for t1, t2 in roundRobinPair(nTeam1, nTeam2, nMatch):
        matchCount[t1, t2] += 1
    print(matchCount)
    print(matchCount.sum(1))
    print(matchCount.sum(0))


class Division:
    """
    This represents a pool of team that will play against each other.
    """
    def __init__(self, name, teamL=[]):
        self.name = name
        self.teamL = list(teamL)
        self.teamL.sort(key=teamSortKey)
        self.rank = self.teamL[0].rank

    def getMatchL(self, nMatch):
        """
        Basic round robin matching. n*(n-1)/2 match.
        """
        matchL = []

        for idx1, idx2 in roundRobin(len(self.teamL), nMatch):
            matchL.append(Match(self.teamL[idx1], self.teamL[idx2]))

        return matchL

    def getMatchTable(self, nMatch):
        matchL = self.getMatchL(nMatch)

        matchCount = {}
        for team1 in self.teamL:
            for team2 in self.teamL:
                matchCount[(team1, team2)] = 0

        for match in matchL:
            matchCount[match.team1, match.team2] += 1
            matchCount[match.team2, match.team1] += 1

        return matchCount

    def key(self):
        return self.name

    def __str__(self):
        return '%s (%d teams)' % (self.name, len(self.teamL))


class DivisionHalf(Division):

    def __init__(self, name, teamL1, teamL2):
        self.name = name
        self.teamL1 = list(teamL1)
        self.teamL2 = list(teamL2)
        self.teamL1.sort(key=teamSortKey)
        self.teamL2.sort(key=teamSortKey)
        self.rank = min(self.teamL1[0].rank, self.teamL2[0].rank)

    def getMatchL(self, nMatch):
        matchL = []
        for idx1, idx2 in roundRobinPair(len(self.teamL1), len(self.teamL2), nMatch):
            matchL.append(Match(self.teamL1[idx1], self.teamL2[idx2]))
        return matchL

    def getMatchTable(self, nMatch):
        matchL = self.getMatchL(nMatch)

        matchCount = {}
        for team1 in self.teamL1:
            for team2 in self.teamL2:
                matchCount[(team1, team2)] = 0

        for match in matchL:
            matchCount[match.team1, match.team2] += 1

        return matchCount

    def _getTeamL(self):
        return list(self.teamL1) + list(self.teamL2)

    teamL = property(_getTeamL)

    def __str__(self):
        return '%s (%d team1, %d team2)' % (self.name, len(self.teamL1), len(self.teamL2))


class Team:
    def __init__(self, name=""):
        self.name = name
        self.playerL = []
        self.division= None
        self.rank = None

    def key(self):
        return self.name.lower()

    def __str__(self):
        return self.name


class Restriction:
    def __init__(self, include, value, team, date):
        self.include = include
        self.value = value
        self.team = team
        self.date = date

        self.timeMax = None
        self.timeMin = None
        self.stadiumS = None
        self.fNameS = None

    def isActive(self, field):
        ok = True
        try:
            ok &= field.stadium in self.stadiumS
        except TypeError:
            pass
        try:
            ok &= field.name in self.fNameS
        except TypeError:
            pass

        if self.timeMax is not None:
            ok &= field.time <= self.timeMax
        if self.timeMin is not None:
            ok &= field.time >= self.timeMin

        return self.include ^ ok

    def getPen(self, field):
        if self.isActive(field):
            return self.value
        else:
            return 0

    def __str__(self):
        restrL = []
        if self.timeMin is not None or self.timeMax is not None:
            s = ''
            if self.timeMin is not None:
                s += str(self.timeMin)
            s += '...'
            if self.timeMax is not None:
                s += str(self.timeMax)
            restrL.append(s)

        if self.stadiumS is not None:
            restrL.append(str(self.stadiumS))

        if self.fNameS is not None:
            restrL.append(str(self.fNameS))

        d = {True: 'include', False: 'exclude'}

        return "restr %s %.3g %s @ %s %s" % (
            d[self.include], self.value, self.team, self.date, ', '.join(restrL))


class TeamGrpConflict:
    def __init__(self, sameDate=True, dt=0, sameStadium=True):
        self.sameDate = sameDate
        self.dt = dt  # dt is in minutes
        self.sameStadium = sameStadium
        self.penRatio = self._getPenRatio()

    def hasConflict(self):
        return self.penRatio >= 1.

    def _getPenRatio(self):
        if not self.sameDate:
            return 0

        dt = self.dt
        if not self.sameStadium:
            if dt >= 60:
                pen = 0.3  # playable but not cool !
            else:
                pen = 1.  # not playable
        else:
            if dt < -15:
                pen = 1.  # not playable
            elif dt < 0:
                pen = 0.5  # 15 minutes overlap ... not so bad :p
            elif dt > 60.*5.:
                pen = 0.3  # playable but over 5h delay
            else:
                pen = 0.3 * dt/(60.*5.)  # penalty is linearly proportional to delay

        return pen


class Config:
    """
    There are 4 kinds of restrictions that are taken into account in the schedule generator.
    * Built-in restriction : One team should not play two game at the same date
    * Field related penalties : penalties incurred when a particular team play on a particular field
    * Multi-team restrictions : penalties incurred when a player that plays in more than one team would have a conflict
    * Uniformity penalties : penalties incurred when some teams have too many games in a generally inconvenient field.

    """
    def __init__(self, league, fieldL, restrD, grpD, unifL, matchDuration, nbMatch, penDateFactor):
        self.league = league
        self.fieldL = makeMap(fieldL)
        self.restrD = restrD
        self.grpD = grpD
        self.unifL = unifL
        self.teamL = league.getTeamL()
        self.penDateFactor = penDateFactor
        self.nMatch = nbMatch
        self.penDateFactor = penDateFactor
        self.matchDuration = matchDuration
        self._makeList()

        self.restrL = []
        for restr in self.restrD.values():
            self.restrL += restr

    def _makeList(self):
        self.dateL = makeMap(set([field.date for field in self.fieldL]))
        self.divL = makeMap(set([team.division for team in self.teamL]))

    def getPenMat(self):
        """penMat[ team, field ] represents the penalty incurred when this team plays on this field.
        This is a static matrix which contains all restrictions of the first kind.

        """
        penMat = np.zeros((len(self.teamL)+1, len(self.fieldL)))
        # add one more team so that penMat[ -1, : ] = 0. This is useful since team -1 represents a free field.
        for team in self.teamL:
            for field in self.fieldL:
                pen = 0
                for restr in self.restrD.get((team, field.date), []):
                    pen += restr.getPen(field)
                penMat[team.idx, field.idx] = pen

        return penMat

    def getGrpList(self):
        grpL = []
        for pen, teamL in self.grpD.values():
            grpL.append((pen, [team.idx for team in teamL]))
        grpL = np.array(grpL, dtype=object)  # transform into numpy array so we can batch-index elements.
        return grpL

    def getGrpPen(self):
        """grpPenMat[ field, field ] provides the penalty incurred when a player is playing on those two fields on the same date
        (a player that is part than more than one team). To obtain the penalty related to more than two teams,
        we sum all possible pairs of fields.

        The result is a symmetric field x field matrix.
        When it is not playable (big time overlap), penalty is 1.
        when it is playable but with a gap of 5h or on different stadium, the penalty is 0.3
        When it is in the same stadium, the penalty range from 0 to 0.3 depending on the time gap
        """
        n = len(self.fieldL)
        penMat = np.zeros((n, n))

        grpConflictMat = self.getGrpConflictMat()

        for i in range(n):
            penMat[i, i] = 1.
            for j in range(i):

                grpConflict = grpConflictMat[i, j]
                if grpConflict is None:
                    continue
                else:
                    pen = grpConflict.penRatio
                    penMat[i, j] = pen
                    penMat[j, i] = pen

        return penMat

    def getGrpConflictMat(self):
        """grpPenMat[ field, field ] provides the penalty incurred when a player is playing on those two fields on the same date
        (a player that is part than more than one team). To obtain the penalty related to more than two teams,
        we sum all possible pairs of fields.

        The result is a symmetric field x field matrix.
        When it is not playable (big time overlap), penalty is 1.
        when it is playable but with a gap of 5h or on different stadium, the penalty is 0.3
        When it is in the same stadium, the penalty range from 0 to 0.3 depending on the time gap
        """
        n = len(self.fieldL)
        conflictMat = np.zeros((n, n), dtype=object)
        conflictMat[:] = None

        for i in range(n):
            for j in range(i):
                fieldA = self.fieldL[i]
                fieldB = self.fieldL[j]

                if fieldA.date != fieldB.date:
                    continue  # not the same day => no conflict

                if fieldA.time > fieldB.time:  # makes sure that fieldA starts before FieldB
                    fieldA, fieldB = fieldB, fieldA

                dt = fieldB.time - fieldA.endTime  # time gap

                teamGrpConflict = TeamGrpConflict(True, dt, fieldA.stadium == fieldB.stadium)

                conflictMat[i, j] = teamGrpConflict
                conflictMat[j, i] = teamGrpConflict

        return conflictMat

    def getUnifStruct(self):
        """
        unifMagL is the magnitude of the exponential penalty for the uniformity penalties.
        unifFieldGrpMap is a map from field index to list of active group
        pastUnifCount is the cumulated count from past games for each team
        """

        idSet = set([el[0] for el in self.unifL])
        idMap = dict(zip(list(idSet), range(len(idSet))))

        unifMagL = [0.] * len(idSet)
        for id_, mag, _restr in self.unifL:
            unifMagL[idMap[id_]] = mag

        unifFieldGrpMap = []
        for field in self.fieldL:
            grpSet = set()
            for id_, mag, restr in self.unifL:
                if restr.isActive(field):
                    grpSet.add(idMap[id_])
            unifFieldGrpMap.append(list(grpSet))

        pastUnifCount = np.zeros((len(idMap), len(self.teamL)+1), dtype=int)
        for team in self.teamL:
            if hasattr(team, 'unifCountD'):
                for id_, count in team.unifCountD.items():
                    pastUnifCount[idMap[id_], team.idx] = count

        return np.asarray(unifMagL), unifFieldGrpMap, pastUnifCount, idMap

    def getFieldDateMap(self):
        """
        fieldDate is a map that provides the date idx of a particular field
        (since field is a combination of stadium, fieldName, date and time.
        """
        return np.array([field.date.idx for field in self.fieldL])

    def randomScheduleMat(self):
        matchL = []
        fieldIdx = 0
        for match in self.league.getMatchL(self.nMatch):
            tMatch = (fieldIdx, match.team1.idx, match.team2.idx)
            fieldIdx += 1
            matchL.append(tMatch)

        print('Number of fields : %d, number of match : %d' % (len(self.fieldL), len(matchL)))
        if len(self.fieldL) < len(matchL):
            eStr = 'not enough fields. Number of fields : %d, number of match : %d' % (
                len(self.fieldL), len(matchL))
            raise Exception(eStr)
        else:
            for fieldIdx_ in range(fieldIdx, len(self.fieldL)):
                matchL.append((fieldIdx_, -1, -1))

        scheduleMat = np.array(matchL, dtype=int)
        return scheduleMat

    def getScheduleFromMat(self, schMat):
        matchL = []
        for fieldIdx, team1Idx, team2Idx in schMat:
            if team1Idx == -1:
                continue
            match = Match(self.teamL[team1Idx], self.teamL[team2Idx])
            match.field = self.fieldL[fieldIdx]
            matchL.append(match)

        return matchL


class ObjSrv:
    def __init__(self):
        self.idx = 0
        self.objD = {}
        self.lock = False

    def __getitem__(self, obj):
        try:
            return self.objD[obj.key()]  # try to return an object of the same key
        except KeyError:
            if self.lock:
                raise Exception('Objet inconnu : %s' % str(obj))
            else:
                self.objD[obj.key()] = obj
                obj.idx = self.idx
                self.idx += 1
            return obj

    def values(self):
        l = [None]*len(self.objD)
        for e in self.objD.itervalues():
            l[e.idx] = e
        return l


def makeMap(itemSet):
    itemL = list(itemSet)
    itemL.sort(key=lambda x: x.key())
    for idx, item in enumerate(itemL):
        item.idx = idx
    return itemL


def orderList(objL):
    newL = [None]*len(objL)
    for obj in objL:
        newL[obj.idx] = obj
    return newL


if __name__ == "__main__":
    testRoundRobinPair()

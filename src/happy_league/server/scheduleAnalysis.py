'''
Created on 2011-11-02

@author: alexandre
'''


import numpy as np

class AnalysisResult:
    
    def __init__(self, config, matchL, optState ):
        self.config = config
        self.matchL = matchL
        self.optState = optState
        
        self.conflictMatchD = self.analyseRestr()
        self.dateTeamSet = self.getDateTeamSet()
        self.countD = self.analyseSingleMatch()
        self.unifCountD, self.unifCountHistD = self.analyseUniformity()
        self.grpConflictMat = self.config.getGrpConflictMat()
        self.teamGrpConflictD = self.analyseTeamGroup()

    def getDateTeamSet(self):
        teamDateSet = {}
        for date in self.config.dateL:
            for team in self.config.teamL:
                teamDateSet[(date,team)] = set()
                
        for match in self.matchL:     
            date = match.field.date
            teamDateSet[ (date, match.team1) ].add( match )
            teamDateSet[ (date, match.team2) ].add( match )
            
        return teamDateSet 

    def analyseRestr(self):
        conflictMatchD = {}
        restrD = self.config.restrD
        for match in self.matchL:
            date = match.field.date
            team1, team2 = match.team1, match.team2
            restrL = restrD.get( (team1,date), [] ) + restrD.get( (team2,date), [] )
            for restr in restrL:
                if restr.isActive(match.field):
                    try:             conflictMatchD[match].append(restr)
                    except KeyError: conflictMatchD[match] = [restr]
                    
        return conflictMatchD
    
    def analyseSingleMatch(self):
        countD = {}
        for key, matchSet in self.dateTeamSet.items():
            countD[key] = len(matchSet)
        return countD
    
    def analyseUniformity(self):
        
        # initialize unifCountD to 0
        unifCountD = {}
        for id_, _mag, _restr in self.config.unifL:
            for team in self.config.teamL:
                unifCountD[ (id_,team) ] = 0
        
        # add the pastUnifCount
        for team in self.config.teamL:
            if hasattr( team, 'unifCountD'):
                for id_, count in team.unifCountD.items():
                    unifCountD[ (id_,team)  ] = count
                    
        # increment values of unifCountD
        for match in self.matchL:
            for id_, mag, restr in self.config.unifL:
                if restr.isActive(match.field):
                    unifCountD[ (id_, match.team1) ] += 1
                    unifCountD[ (id_, match.team2) ] += 1
        
        
        # transform into countLD 
        maxCount = max(unifCountD.values())
        countLD = {} 
        for key, count in unifCountD.items():
            countLD.setdefault(key[0],[]).append( count )
        # make an histogram
        countHistD = {}
        for id_, valL in countLD.items():
#            print id_, valL
            bincount = np.bincount( valL )
            dLen =  maxCount+1 - len(bincount)
            if dLen > 0:
                bincount = np.concatenate( ( bincount, np.zeros( dLen, dtype=int ) ) )
            countHistD[id_] =  bincount
#        print countHistD
        return unifCountD, countHistD
    
    def analyseTeamGroup(self):
        conflictD = {}
        for grpId, grpData in self.config.grpD.items():
            _pen, teamL = grpData
            conflictD[grpId] = []
            for date in self.config.dateL:
                matchL = []
                for team in teamL:
                    matchL += list( self.dateTeamSet[(date,team)] )
                
                for i in range(len(matchL)):
                    for j in range(i):
                        matchA, matchB = matchL[i], matchL[j]
                        conflict = self.grpConflictMat[ matchA.field.idx, matchB.field.idx ]
                        if conflict is not None:
                            conflictD[grpId].append( ( conflict, matchA, matchB ) )
                        
        return conflictD
    
    def __str__(self):
        
        strL= []

        strL.append( "Match count for the same team on the same day :")
        for key, count in self.countD.items():
            if count > 1:
                date, team = key
                strL.append( "%s plays %d match on %s"%(team, count, date) )
        
        strL.append('\n')
        
        strL.append( "Unsatisfied restrictions" )
        for match, restrL in self.conflictMatchD.items():
            penL = [ "%.1f"%restr.value for restr in restrL ]
            strL.append( "%s -> %s"%( str(match), ' + '.join( penL )) )
        
        strL.append('\n')
        
        return '\n'.join(strL)
        


            
        
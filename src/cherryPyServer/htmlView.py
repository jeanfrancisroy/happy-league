'''
Created on 2011-11-02

@author: alexandre
'''

from table import TableMap
from model import makeMap,teamSortKey
from util import formatDelay
from xlsConfig import unparseTime
from scheduleAnalysis import AnalysisResult
import numpy as np
from copy import deepcopy

sortKey = lambda x:x.key

class HtmlSchedule:
    
    def __init__(self, config, matchL, optState):
        self.matchL = matchL
        self.config = config
#        dateL = []
#        divL = []
        self.schDateDiv = {}

#        for match in matchL:
#            div = match.team1.division
#            assert div == match.team2.division
#            dateL.append(  match.field.date )
#            divL.append( div )
            
                        
#        self.dateL = makeMap( set( dateL ) )
#        self.divL = makeMap( set( divL ) )
        
        for date in self.config.dateL:
            for div in self.config.divL:
                self.schDateDiv[ (date,div) ] = []
        
        for match in matchL:
            div = match.team1.division
            date = match.field.date
            
            self.schDateDiv[ ( date, div ) ].append( match )
        
    def __html__(self):
        
        objL = []
        
        remainingFieldSet = set(self.config.fieldL)

        for i,date in enumerate(self.config.dateL):
            
            dateStr =  'date %d : %s'%(i+1,date)
            objL.append( HtmlTag( 'h2', dateStr  )  )
            
            d = {}
            count = 0
            for div in self.config.divL:
                for match in self.schDateDiv[(date, div)]:
                    count +=1
                    assert match.field.date is date
                    
                    time = '%d:%02d'%unparseTime(match.field.time)
                    court   = match.field.name
                    stadium = match.field.stadium
                    
                    remainingFieldSet.remove( match.field )
                    if not d.has_key(stadium): d[stadium] = {}
                    d[stadium][(time,court)] = '%s<font color="gray" size="-1" ><br> vs <br></font>%s'%(match.team1.name, match.team2.name)
            
            for field in remainingFieldSet:
                if field.date is not date: continue
                time = '%d:%02d'%unparseTime(field.time)
                d[field.stadium][(time,field.name)] = """<font color="gray" >AVAILABLE</font>"""
            
            for stadium, table in d.iteritems():
                objL.append( HtmlTag( 'h3', stadium   )  )
                colL = TableMap(table).toStrMat()
                objL.append( HtmlTable(zip(*colL), [{'align':'center'}]*len(colL),  border="1", cellpadding="3", cellspacing="0") )

        
        return '\n'.join( [ obj.__html__() for obj in objL ] )

class HtmlConfig:
    def __init__(self,config, *argL):
        self.config = config
        self.objL = self.generalConf()
        self.objL += self.matchTable()
    
    def generalConf(self):
        objL = []
        objL.append( HtmlTag( 'h2', 'General parameters'  )  )
        rowL = []
        rowL.append( [ Bold('Match duration'), formatDelay( self.config.matchDuration * 60. ) ])
        rowL.append( [ Bold('Number of match'), str( self.config.nMatch ) ])
        rowL.append( [ Bold('Double match penalty'), "%.3g"%( self.config.penDateFactor ) ])
        
        objL.append( HtmlTable(rowL, [{'align':'right'}, {'align':'left'} ], cellpadding="3", cellspacing="0") )
        return objL
    
    def matchTable(self):
        objL = []
        objL.append( HtmlTag('h2','Match table') )
        for division in self.config.league.divisionL:
            objL.append( HtmlTag('h3',division.name) )
            
            matchTable = division.getMatchTable( self.config.nMatch )
            
            
            objL.append( HtmlTableMap( { "cellpadding":"10", "cellspacing":"0", 'border':'1'}, 
                    matchTable, rowSortKey=teamSortKey, colSortKey=teamSortKey) )
                
#        return  [ HtmlTag('div', *objL, style="text-align:center;") ]
        return objL

    
    def __html__(self):
        return '\n'.join( [ obj.__html__() for obj in self.objL ] ) 

class HtmlAnalysis(AnalysisResult):
    
    def __init__(self,config, matchL, optState):
        AnalysisResult.__init__( self, config, matchL, optState)
        self._buildHtml()
    
    
    def _buildHtml(self):
        self.objL = []
        
        # statistics 
        self.objL.append( HtmlTag('h2', 'Statistics') )
        rowL = []
        rowL.append( [ Bold('Number of Teams'), "%d"%len(self.config.teamL) ])
        rowL.append( [ Bold('Number of Dates'), "%d"%len(self.config.dateL) ])
        rowL.append( [ Bold('Number of Divisions'), "%d"%len(self.config.divL) ])
        rowL.append( [ Bold('Number of Fields'), "%d"%len(self.config.fieldL) ])
        nMatch = len([match for match in self.matchL if match.team1 != -1 ])
        rowL.append( [ Bold('Number of match'), "%d"%nMatch ])
        self.objL.append(HtmlTable(rowL, [{'align':'right'}, {'align':'left'} ], cellpadding="1", cellspacing="0"))
        
        # optimizer 
        self.objL.append( HtmlTag('h2', 'Optimizer') )
        self.objL.append(self.optState)
        
        
        # Conflicting overview
        self.objL.append( HtmlTag('h2', 'More than one game on the same date') )
        if  max(self.countD.values())  <= 1: 
            self.objL.append( Font('Congratulations ! No conflict.', color="Green"))
        else:           
            
            table ={}
            for i,n in enumerate( np.bincount( self.countD.values() ) ):
                key = "%d game on the same date"%i
                table[ ( key, 'occurence' ) ] = n  
                if i > 1 : penalty = self.config.penDateFactor * (i-1) * n
                else : penalty = 0 
                table[ ( key, 'penalty' ) ] = "%.3g"%penalty   
            self.objL.append( HtmlTableMap( {}, table) )
            
        # Unsatisfied restriction
        self.objL.append( HtmlTag('h2', 'Unsatisfied restriction') )
        if len( self.conflictMatchD ) == 0:
            self.objL.append( Font('Congratulations ! All restrictions are satisfied.', color="Green"))
        else:
            strMat = [['<b>Match</b>', '<b>Field</b>', '<b>Penalty</b>']]
            matchL= self.conflictMatchD.keys()
            matchL.sort(key=lambda x: x.key())
            for match in matchL:
                restrL = self.conflictMatchD[match]
                penL = [ "%.1f"%restr.value for restr in restrL ]
                vs = '%s<font color="gray" size="-1" > vs </font>%s'%(match.team1.name, match.team2.name)
                strMat.append( [ vs, unicode(match.field), ' + '.join( penL )  ] )
            self.objL.append(HtmlTable(strMat, cellpadding="10", cellspacing="0"))
        

        
        # Uniformity
        self.objL.append( HtmlTag('h2', 'Uniformity histogram') )
        table = {}
        for id_, hist, in self.unifCountHistD.items():
            for i, count in enumerate(hist):
                table[id_,i] = count
        self.objL.append( HtmlTableMap({}, table) )
        
    def __html__(self):
        return '\n'.join( [ obj.__html__() for obj in self.objL ] )

class HtmlTeamGroup(HtmlAnalysis):
    
    def _buildHtml(self):
        self.objL = []
        
        self.objL.append( HtmlTag('h2', 'Team group conflicts'))
        
        conflictInfoTable = {}
        colL = [ 'nb conflicts', 'nb overlap', 'avg time gap' , 'cum penalty'  ]
        penRowL = []
        for grpId, conflictL in self.teamGrpConflictD.items():
            (mag, _teamL ) = self.config.grpD[grpId]
            dtL = []
            conflictCount = 0
            negDtL = []
            cumPen = 0
            for conflict, _matchA, _matchB in conflictL :
                if conflict.hasConflict() :
                    conflictCount += 1
                elif conflict.dt < 0: 
                    negDtL.append( conflict.dt )
                else : 
                    dtL.append( conflict.dt )
                cumPen += mag * conflict.penRatio
            
            if len(dtL) == 0: waitingTime = 0
            else :            waitingTime = float(sum(dtL))/len(dtL)
            
#            print 'type(grpId)', type(grpId)
            conflictInfoTable[ (grpId,colL[0])] = conflictCount
            conflictInfoTable[ (grpId,colL[1])] = len(negDtL)
            conflictInfoTable[ (grpId,colL[2])] = formatDelay( waitingTime *60) 
            conflictInfoTable[ (grpId,colL[3])] = cumPen
            penRowL.append( ( cumPen, grpId ) )
        
        penRowL.sort(reverse=True)
        rowL = [ grpId for _pen,grpId in penRowL ]
        self.objL.append( HtmlTableMap( {"cellpadding":"5", "cellspacing":"0"}, conflictInfoTable, rowL=rowL, colL = colL ))

class HtmlConflict(HtmlAnalysis):
    
    def _buildHtml(self):
        self.objL = []
        
        # Conflicting match
        self.objL.append( HtmlTag('h2', 'More than one game on the same date.') )
        if  max(self.countD.values())  <= 1: 
            self.objL.append( Font('Congratulations ! No conflict.', color="Green"))
        else:
            strMat = [['<b>Team</b>', '<b>Date</b>', '<b>Count</b>', '<b>Penalty</b>']]
            for key, count in self.countD.items():
                if count > 1:
                    date, team = key
                    strMat.append( [team.name, str(date), str(count), "%.3g"%((count-1)*self.config.penDateFactor) ] )
            self.objL.append(HtmlTable(strMat, cellpadding="10", cellspacing="0"))


class HtmlRestriction(HtmlAnalysis):
    
    def _buildHtml(self):
        self.objL = []
        
        # Unsatisfied restriction
        self.objL.append( HtmlTag('h2', 'Unsatisfied restriction') )
        if len( self.conflictMatchD ) == 0:
            self.objL.append( Font('Congratulations ! All restrictions are satisfied.', color="Green"))
        else:
            strMat = [['<b>Match</b>', '<b>Field</b>', '<b>Penalty</b>']]
            matchL= self.conflictMatchD.keys()
            matchL.sort(key=lambda x: x.key())
            for match in matchL:
                restrL = self.conflictMatchD[match]
                penL = [ "%.1f"%restr.value for restr in restrL ]
                vs = '%s<font color="gray" size="-1" > vs </font>%s'%(match.team1.name, match.team2.name)
                strMat.append( [ vs, "%s"%match.field, ' + '.join( penL )  ] )
            self.objL.append(HtmlTable(strMat, cellpadding="10", cellspacing="0"))




class HtmlUniformity(HtmlAnalysis):
    
    def _buildHtml(self):
        self.objL = []
        
        # Unsatisfied restriction
        self.objL.append( HtmlTag('h2', 'Uniformity counts for each team') )
        
        
        pastUnifCountT = {}
        
        teamCaptionD = {}
        for team in self.config.teamL:
            teamCaptionD[team.rank]= team.name
            if hasattr( team, 'unifCountD'):
                for id_, count in team.unifCountD.items():
                    pastUnifCountT[ (team.rank, id_)  ] = count
        
        unifCountT = deepcopy( pastUnifCountT )
        
        idSet = set()
        for match in self.matchL:
            for id_, _mag, restr in self.config.unifL:
                idSet.add(id_)
                if restr.isActive(match.field):
                    try:              unifCountT[ (match.team1.rank, id_)] += 1
                    except KeyError : unifCountT[ (match.team1.rank, id_)]  = 0
                    try :             unifCountT[ (match.team2.rank, id_)] += 1
                    except KeyError : unifCountT[ (match.team2.rank, id_)]  = 0
        
        for key, count in pastUnifCountT.items():
            rank, id_ = key
            unifCountT[ rank, u"(%s)"%id_ ] = count
        
        alignDL = [{'align':'right'}] + [{'align':'center'}]*len(idSet)*2
        htmlTable = HtmlTableMap( {"colAttrDL":alignDL}, unifCountT )
        htmlTable.formatInfo( rowCaption=teamCaptionD.get )
        self.objL.append( htmlTable )

class HtmlTableMap(TableMap):
    
    def __init__(self, htmlAttrD, *argL, **argD):
        TableMap.__init__(self, *argL, **argD)
        self.htmlAttrD = htmlAttrD
    
    def __html__(self):

        strMat = self.toStrMat()        
        strMat[0] = [ Bold(cell) for cell in strMat[0] ] # bold row header
        strMat = zip(*strMat) # transpose (we have to do it anyway)
        strMat[0] = [ Bold(cell) for cell in strMat[0] ] # bold col header
        
#        strMat = np.array(strMat)

        htmlTable = HtmlTable(strMat, **self.htmlAttrD)

        return htmlTable.__html__()
        



class HtmlTable:
    
    def __init__(self, strMat, colAttrDL=None, rowAttrDL=None, **attrD ):
        self.tableTag = HtmlTag('TABLE', **attrD)
        nCol = max([len(row) for row in strMat ])
        nRow = len(strMat)
        if colAttrDL is None: colAttrDL = [{'align':'center'}]*nCol
        if rowAttrDL is None: rowAttrDL =  [{}]*nRow
        for row,rowAttrD in zip( strMat, rowAttrDL ):
            rowTag = HtmlTag('TR', **rowAttrD)
            for cell,colAttrD in zip(row,colAttrDL):
                rowTag.add( HtmlTag('TD', cell, **colAttrD) )
            self.tableTag.add( rowTag )
        
    def __html__(self):
        return self.tableTag.__html__()

class HtmlTag:
    
    def __init__( self, tag, *objL, **attrD ):
        self.tag = tag
        if attrD is None : attrD = {}
        self.attrD = attrD
        self.objL = objL
    
    def add(self, *objL):
        self.objL += objL
    
    def __html__(self):
        attrL = [ '%s="%s"'%(key,val) for key, val in self.attrD.items() ]
        strL = ["<%s %s>"%(self.tag, ' '.join(attrL) )]
        for obj in self.objL:
            if isinstance(obj, (str, unicode)): 
                strL.append( obj )
            else:
                strL.append( obj.__html__() )
        strL.append( "</%s>"%self.tag) 
        return '\n'.join( strL)
    
class Bold(HtmlTag):
    def __init__(self, *objL, **attrL):
        HtmlTag.__init__(self,'b', *objL, **attrL)

class Font(HtmlTag):
    def __init__(self, *objL, **attrL):
        HtmlTag.__init__(self,'font', *objL, **attrL)


class HtmlEncode:
    def __init__(self,coding='UTF-8'):
        self.s = """<meta http-equiv="Content-Type" content="text/html; charset=%s"/> """%coding
        
    def __html__(self):
        return self.s

class HtmlRefresh:
    def __init__(self,delay=1):
        self.s = """<META HTTP-EQUIV="REFRESH" CONTENT="%f"> """%delay
        
    def __html__(self):
        return self.s

class HtmlDoc:
    
    def __init__(self, *objL):
        self.head = HtmlTag('HEAD',HtmlEncode())
        self.body = HtmlTag('BODY', *objL)
        self.doc = HtmlTag( 'HTML', self.head, self.body )
    
    def add(self, *objL):
        self.body.objL += objL
    
    def __html__(self):
        return self.doc.__html__()
    
    def write(self,filePath):
        with open( filePath, 'w' ) as fd:
            fd.write(self.doc.__html__()) 
            
            
if __name__ == "__main__":
    doc = HtmlDoc()
    doc.add('allo <font color="gray" size="-1" > mon </font> coco 2')
    doc.add( HtmlTag( 'p', 'test', color="Green"))
    table = {}
    table[('a','1')] = 3
    table[('b','2')]= 4
    table[('b','1')]= 1
    
    doc.add( HtmlTable( TableMap(table).toStrMat(), border="1" ) )
    print doc.doc.__html__()
    

    doc.write('test.html')
    
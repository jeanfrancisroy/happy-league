# -*- coding: utf-8 -*-
"""
Created on Jan 11, 2011

@author: alex

"""
from future.utils import iteritems
import xlrd
import datetime
import itertools
from model import Field, Restriction, Date, ObjSrv, Team, Division, League, Config, DivisionHalf
from util import parseTime

# Python 3 compatibility
import sys
if sys.version_info > (3, 0):
    unicode = str


TEAM = 'equipe'
STADIUM = 'stade'
TIME = 'heure'
TIME_MAX = 'heure max'
TIME_MIN = 'heure min'
DATE = 'date'
FNAME = 'terrain'

typeL = (TEAM, STADIUM, TIME, FNAME, STADIUM, DATE)

confKeyMap = {
    u'Durée des match': 'matchDuration',
    u'Nombre de match': 'nbMatch',
    u'Pénalité match double': 'penDateFactor'}

RESTR = u'contraintes'
TEAM_GROUP = u'multi-équipe'
CONF_SHEET = u'Général'
LEAGUE = u'Équipes'
UNIF = u'uniformité'

signD = {'inclusion': True, 'exclusion': False}


def isGroupName(name):
    if not isinstance(name, (str, unicode)): return False
    name = name.strip()
    if len(name) <= 2: return False
    return name[0] == '<' and  name[-1] == '>'


def identity(val): return val


class ConfigException(Exception):
    pass


class ConfigLoader:
    def __init__(self, fileName):

        self.parserD = {
            DATE: self.parseDate,
            TIME: parseTime,
            FNAME: identity,
            STADIUM: identity,
            'action': identity,
            TIME_MAX: parseTime,
            TIME_MIN: parseTime,
            TEAM: self.parseTeam,
            }

        self.dateSrv = ObjSrv()

        self.wb = xlrd.open_workbook(fileName)

        self.loadGeneralConf()
        self.parseLeague()
        self.getGroups()
        self.getFieldL()
        self.getRestriction()
        self.getTeamGrpD()
        self.parseUniformity()

    def parseDate(self, date):
        if isinstance(date, datetime.date):
            d = Date(date.year, date.month, date.day)
        else:
            month, day, year = date.split('/', 2)
            d = Date(int(year), int(month), int(day))
        return self.dateSrv[d]

    def parseTeam(self, teamName):
        if isinstance(teamName, Team):
            team = teamName
        else:
            team = Team(teamName)

        return self.teamSrv[team]

    def loadLeague(self, league):
        self.divSrv = ObjSrv()
        self.teamSet = set()
        for division in league.divisionL:
            division = self.divSrv[division]
            for team in division.teamL:
                self.teamSet.add(team)

    def xl2py(self, val, fmt, strip=False ):
        if fmt == xlrd.XL_CELL_DATE:
            dateTuple = xlrd.xldate_as_tuple(val, self.wb.datemode)
            if dateTuple[3:] == (0,0,0):
                return datetime.date( *dateTuple[:3] )
            elif dateTuple[:3] == (0,0,0):
                return datetime.time( *dateTuple[3:] )
            else:
                return datetime.datetime( *dateTuple  )
        elif fmt == xlrd.XL_CELL_NUMBER:
            return val
        elif fmt == xlrd.XL_CELL_TEXT:
            if strip: val = val.strip()
            return val
        elif fmt == xlrd.XL_CELL_EMPTY:
            return None
        else:
            raise Exception( 'Unknown format %d'%fmt )

    def getRow( self, sh, idx, strip = False ):
        valL = []
        for val, fmt  in zip( sh.row_values(idx), sh.row_types(idx)  ):
            valL.append( self.xl2py( val, fmt, strip ) )
        return valL

    def getGroups( self ):

        sh = self.wb.sheet_by_name(u'groupes')
        groupD = {}

        for division in self.divSrv.objD.values():
            groupD[ '<%s>'%division.name ] = (TEAM,division.teamL)

        for i in range(1,sh.nrows):
            valL = self.getRow( sh, i, True )
            type_ = valL[0]
            name = valL[1]

            if type_ not in typeL:
                raise ConfigException("%s n'est pas un type valide. Les valeurs possibles sont : %s."%(type_, ', '.join(typeL)) )
            if not isGroupName(name):
                raise ConfigException("Un nom de groupe doit commencer par '<' et terminer par '>', ce qui n'est pas le cas de :%s"%name)

            itemL = []
            for val in valL[2:]:
                if val is not None: itemL.append( val )

            groupD[name] = (type_,itemL)


        self.groupD = groupD

    def expand( self, field, type_ ):
        if field is None: return None
        if not isinstance(field, (str, unicode)):
            valL = [field]
        else:
            if isGroupName( field ) and field in self.groupD:
                (type__, valL ) = self.groupD[ field ]
                if type__ != type_:
                    raise Exception("Vous avez utilisé un groupe de type %s dans un champ de type %s"%(type__,type_) )
            elif ',' in field:
                valL = [ val.strip() for val in field.split( ',' ) ]
            else:
                valL = [field]

        return [ self.parserD[type_]( val ) for val in valL ]

    def expandAll( self, valL, type2idx, typeL ):
        valLL = []
        for type_ in typeL:
            idx = type2idx[type_]
            valLL.append( self.expand( valL[idx], type_ ) )
        return valLL

    def getRestriction(self):
        sh = self.wb.sheet_by_name(RESTR)

        typeL, type2idx = self.getType( sh )

        restrD = {}

        self.teamSrv.lock = True
        self.dateSrv.lock = True

        for i in range(1,sh.nrows):
            valL = self.getRow( sh, i, True )
            include = signD[ str(valL[0]).strip() ]
            value = valL[1]

            teamL, dateL = self.expandAll( valL,type2idx,(TEAM,DATE) )
            timeMinL, timeMaxL, stadiumL, fNameL = self.expandAll( valL,type2idx,(TIME_MIN,TIME_MAX,STADIUM,FNAME) )



            if dateL is None:
                dateL = self.dateSrv.objD.values()

            for team in teamL:
                for date in dateL:
                    restr = Restriction( include, value, team, date )
                    if timeMinL is not None: restr.timeMin  = parseTime(timeMinL[0])
                    if timeMaxL is not None: restr.timeMax  = parseTime(timeMaxL[0])
                    if stadiumL is not None: restr.stadiumS = set( stadiumL )
                    if fNameL   is not None: restr.fNameS   = set( fNameL )
                    try:                restrD[ (team,date) ].append( restr )
                    except KeyError :   restrD[ (team,date) ] = [restr]



        self.restrD = restrD

    def getType(self, sh ):
        typeL = self.getRow( sh, 0, True )
        typeL = [ str(type_) for type_ in typeL ]
        type2idx = dict(  zip( typeL, range(len(typeL)) )  )

        return typeL, type2idx

    def getFieldL(self):
        sh = self.wb.sheet_by_name(u'terrains')
        typeL, _type2idx = self.getType(sh)

        fieldSet = set()
        for i in range(1, sh.nrows):
            valL = self.getRow(sh, i, True)
            action = str(valL[0]).strip()
            fieldPropLL = [self.expand(val, type_) for val, type_ in zip(valL[1:], typeL[1:])]
            subSet = set([fieldProp for fieldProp in itertools.product(*fieldPropLL)])

            if action == '+':
                fieldSet.update(subSet)
            elif action == '-':
                fieldSet.difference_update(subSet)

        fieldL = list(fieldSet)
        fieldL.sort()

        dateL = list(set(list(zip( *fieldL))[1]))
        dateL.sort()

        self.fieldL = []
        for stadium, date, time, fName in fieldL:
            self.fieldL.append( Field( stadium, fName, time, date, self.matchDuration ) )

    def getTeamGrpD(self):
        sh = self.wb.sheet_by_name(TEAM_GROUP)
        teamGrpD = {}
        for i in range(1,sh.nrows):
            valL = self.getRow( sh, i, True )
            name = valL[0]
            pen = valL[1]
            teamL = []
            for teamName in valL[2:]:
                if teamName is not None:
                    team = self.parseTeam(teamName)
                    if team in self.teamSet:
                        teamL.append( team )
                    else:
                        print('Unknown team : %s' % str(team))

            teamGrpD[name] = (pen, teamL)

        self.teamGrpD = teamGrpD

    def parseLeague(self):
        sh = self.wb.sheet_by_name(LEAGUE)
        self.teamSrv = ObjSrv()
        header = self.getRow( sh, 0, True )
        unifGrpIdL = header[3:]
        print(unifGrpIdL)
        divD = {}
        for i in range(1,sh.nrows):
            valL = self.getRow( sh, i, True )
            try:
                div = int(valL[0])
            except ValueError:
                div = str(valL[0])

            pool = valL[1]
            team = self.parseTeam(valL[2])
            team.rank = i
            countL = [ int(e) for e in valL[3:] ]
            team.unifCountD = dict( zip(unifGrpIdL, countL ))
            if div not in divD:
                divD[ div ] = []
            divD[div].append( (pool, team ) )


        divL = []
        for divId, valL in iteritems(divD):
            poolL, teamL = zip( *valL )
            poolS = set(poolL)
            if len(poolS) == 1:
                division = Division('division-%s'%str(divId), teamL)
            elif len(poolS) == 2:
                pool1, pool2 = list(poolS)
                teamL1 = [ team for pool, team in valL if pool == pool1 ]
                teamL2 = [ team for pool, team in valL if pool == pool2 ]
                division = DivisionHalf('division-%s'%str(divId), teamL1, teamL2)
            else:
                raise Exception("Can't have more than two pools in the same division (%s)."%(', '.join(map(str,poolS))) )

            for team in teamL :
                team.division = division
            divL.append( division )

        self.league = League( divL )
        self.loadLeague( self.league )

    def parseUniformity(self):
        sh = self.wb.sheet_by_name(UNIF)
        unifL = []
        for i in range(1,sh.nrows):
            restr = Restriction(False, 1, None, None)
            key, pen, maxCount, timeMin, timeMax, stadium, field = self.getRow(sh, i, True)
            if stadium is not None : restr.stadiumS = set([stadium])
            if field is not None : restr.fNameS = set([field])
            restr.timeMin = parseTime(timeMin)
            restr.timeMax = parseTime(timeMax)
            unifL.append( (key, float(pen) / 2**maxCount, restr) )

        keySet = set(list(zip( *unifL))[0])
        for team in self.league.getTeamL():
            if hasattr( team, 'unifCountD'):
                for id_ in team.unifCountD.keys():
                    if id_ not in keySet:
                        print("Warning : %s not in [%s]" % (id_, ', '.join(list(keySet))))

        self.unifL = unifL

    def loadGeneralConf(self):
        sh = self.wb.sheet_by_name(CONF_SHEET)
        confD = {}
        for i in range(sh.nrows):
            key, val = self.getRow( sh, i, True )
            confD[ confKeyMap[key] ] = val

        self.matchDuration = parseTime( confD['matchDuration'] )
        self.nbMatch = int( confD['nbMatch'] )
        self.penDateFactor = confD['penDateFactor']

    def getConfig(self):
        config = Config(self.league, self.fieldL, self.restrD, self.teamGrpD, self.unifL,
             self.matchDuration, self.nbMatch, self.penDateFactor)
        return config


def testParse():
    config = ConfigLoader('example_configs/xlsConfig.xls').getConfig()
    print(config.fieldL)

if __name__ == "__main__":
    testParse()

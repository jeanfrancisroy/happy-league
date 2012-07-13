#!/usr/bin/env python
'''
Created on Sep 20, 2011

@author: alex

This is a simple script to start schAnneal with $WORK_FOLDER/xlsConfig.xls for $X time
where $WORK_FOLDER is the first argument 
and $X is the second argument in seconds

This script should evolve to be able to have the type of config and the type of optimizer as an argument
'''


import xlsConfig
from annealOpt.schAnneal import SchAnneal
#import model
#from htmlView import HtmlSchedule, HtmlDoc, HtmlAnalysis
#from scheduleAnalysis import AnalysisResult
from os import path
import sys

import numpy as np
np.seterr(over='ignore')



def makeScheduleLeague():
    workFolder = '../example'
    maxTime=20*60 # in seconds

    
    if len(sys.argv) > 1: 
        workFolder = sys.argv[1]
        sys.stdout = open( path.join( workFolder, 'stdout'), 'w' )
        sys.stderr = open( path.join( workFolder, 'stderr'), 'w' )
#        open( path.join(workFolder, 'optimizing') )
        
    if len(sys.argv) > 2: maxTime = float(sys.argv[2])*60


    config = xlsConfig.ConfigLoader(path.join(workFolder,'xlsConfig.xls')).getConfig()
    config.workFolder = workFolder
#    print config.league
    _matchL = SchAnneal(maxTime=maxTime,verbosity=1).opt(config)
#    
#    htmlAnalysis = HtmlDoc()
#    htmlAnalysis.add( HtmlAnalysis( config, matchL) )
#    htmlAnalysis.write('example/analysis.html')
    
#    doc = HtmlDoc()
#    doc.add( HtmlSchedule(matchL) )
#    doc.write('example/schedule.html')

    
if __name__=="__main__":
    makeScheduleLeague()
    
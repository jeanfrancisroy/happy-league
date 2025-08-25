#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sep 20, 2011

@author: alex

This is a simple script to start schAnneal with $WORK_FOLDER/xlsConfig.xls for $X times, where $WORK_FOLDER is the first argument
and $X is the second argument in seconds. This script should evolve to be able to have the type of config and the type of optimizer
as an argument

"""
import xlsConfig
from os import path
import sys

import numpy as np

from happy_league.annealOpt.schAnneal import SchAnneal

np.seterr(over='ignore')


def makeScheduleLeague():
    workFolder = 'example_configs'
    maxTime = 20 * 60  # in seconds

    if len(sys.argv) > 1:
        workFolder = sys.argv[1]
        sys.stdout = open(path.join(workFolder, 'stdout'), 'w')
        sys.stderr = open(path.join(workFolder, 'stderr'), 'w')

    if len(sys.argv) > 2:
        maxTime = float(sys.argv[2]) * 60

    config = xlsConfig.ConfigLoader(path.join(workFolder, 'xlsConfig.xls')).getConfig()
    config.workFolder = workFolder
    _matchL = SchAnneal(maxTime=maxTime,verbosity=1).opt(config)
#
#    htmlAnalysis = HtmlDoc()
#    htmlAnalysis.add( HtmlAnalysis( config, matchL) )
#    htmlAnalysis.write('example/analysis.html')

#    doc = HtmlDoc()
#    doc.add( HtmlSchedule(matchL) )
#    doc.write('example/schedule.html')


if __name__ == "__main__":
    makeScheduleLeague()

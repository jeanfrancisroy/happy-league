#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sep 20, 2011

@author: alex

This is a simple script to start schAnneal with $WORK_FOLDER/xlsConfig.xls for $X times, where $WORK_FOLDER is the first argument
and $X is the second argument in seconds. This script should evolve to be able to have the type of config and the type of optimizer
as an argument

"""
from os import path
import sys

import numpy as np

from happy_league.make_schedule.annealOpt.schAnneal import SchAnneal
from happy_league.shared import xlsConfig

np.seterr(over='ignore')


def makeScheduleLeague(workFolder, maxTime):
    maxTime = float(maxTime) * 60

    orig_stdout = sys.stdout
    orig_stderr = sys.stderr

    with open(path.join(workFolder, 'stdout'), 'w') as stdout:
        with open(path.join(workFolder, 'stderr'), 'w') as stderr:
            sys.stdout = stdout
            sys.stderr = stderr

            try:
                config = xlsConfig.ConfigLoader(path.join(workFolder, 'xlsConfig.xls')).getConfig()
                config.workFolder = workFolder
            except Exception as e:
                sys.stderr.write("Exception during config loading: {}".format(e))
                raise e

            try:
                _matchL = SchAnneal(maxTime=maxTime,verbosity=1).opt(config)
            except Exception as e:
                sys.stderr.write("Exception during optimization: {}".format(e))
                raise e

    sys.stdout = orig_stdout
    sys.stderr = orig_stderr


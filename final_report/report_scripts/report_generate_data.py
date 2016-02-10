# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 15:16:41 2015

@author: karel
"""
import sys
import matplotlib
matplotlib.use('pdf')
#matplotlib.use('Qt4Agg')
import numpy as np
import os
import shutil
#from scipy.io import savemat
from sys import platform
import matplotlib.pyplot as plt
from collections import OrderedDict
sys.path.append("/Users/karel/FORT/FINESSE/karel_tool")
import finesse
import fptool
import asdex
import time
import pickle
tex_path = "/Users/karel/Dropbox/report/Pictures/"
finesse_case_path = "/Users/karel/FORT/FINESSE/finesse_/test_karel/"
mode = "karel_remote"
session = finesse.FinesseSession(finesse_case_path, mode=mode)

boundary = finesse.FinesseInput.read_boundary_file(finesse_case_path + "files/boundary.dat")
input = finesse.FinesseInput.read_input_file(finesse_case_path + "files/finesse_backup.inp")
target = asdex.AsdexDataSet.load_matlab(finesse_case_path + "files/test_eq_AUG30382at2p5.mat")    
finesse_input = finesse.FinesseInput(input, boundary, target.a_0, target.B_phi0)
npoints = [17, 33, 65, 129, 257]
#npoints = [17, 33]
results = {}
    
for npoint in npoints:
    results[npoint] = {}
    finesse_input.NR = finesse_input.NP = finesse_input.NP_INVERSE = finesse_input.NR_INVERSE = npoint
    start = time.time()
    finesse_output = session.run_finesse(finesse_input)  
    end = time.time()
    finesse_output.assume_dp_dF_correct()
    results[npoint]["finesse_output"] = finesse_output
    results[npoint]["time"] = end - start
    print "done"
output = open('data.pkl', 'wb')
pickle.dump(results, output)
output.close()
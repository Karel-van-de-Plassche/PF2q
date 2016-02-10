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
import tools
tex_path = "/Users/karel/Dropbox/report/Pictures/"
finesse_case_path = "/Users/karel/FORT/FINESSE/finesse_/test_karel/"
mode = "karel_remote"
session = finesse.FinesseSession(finesse_case_path, mode=mode)

boundary = finesse.FinesseInput.read_boundary_file(finesse_case_path + "files/boundary.dat")
input = finesse.FinesseInput.read_input_file(finesse_case_path + "files/finesse_backup.inp")
target = asdex.AsdexDataSet.load_matlab(finesse_case_path + "files/test_eq_AUG30382at2p5.mat")    
finesse_input = finesse.FinesseInput(input, boundary, target.a_0, target.B_phi0)
npoints = [17, 33, 65, 129, 257]
np.seterr(all="ignore")
pkl_file = open('data_npoints.pkl', 'rb')
results_output = pickle.load(pkl_file)
pkl_file.close()
time_ = {}
error = {}
for npoint in npoints:
    finesse_input.NR = finesse_input.NP = finesse_input.NP_INVERSE = finesse_input.NR_INVERSE = npoint
    finesse_output = results_output[npoint]["finesse_output"]
    start = time.time()
    for i in range(50):
        estimation_case = finesse_output.assume_dp_dF_correct()
        q_est, I_encl, (B_theta_est, B_phi_est) = estimation_case.estimate_q(finesse_input, mode="full") 
    end = time.time()
    error[npoint] = np.nanmean(tools.relative_error(finesse_output.q_finesse[0,:], -q_est))
    time_[npoint] = (end - start)/50
    print "done"
#output = open('data.pkl', 'wb')
#pickle.dump(results, output)
#output.close()
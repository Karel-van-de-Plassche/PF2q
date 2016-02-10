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
sys.path.append("/Users/karel/FORT/FINESSE/PF2q")
#sys.path.append("D:\Users\karel\Documents\MobaXterm\home\PF2q")
import pf2q.finesse as finesse
import pf2q.asdex as asdex

import pickle
import pf2q.tools as tools
import copy
import collections
tex_path = "/Users/karel/Dropbox/report/Pictures/"
finesse_case_path = "/Users/karel/FORT/FINESSE/finesse_/test_karel/"
mode = "karel_remote"
session = finesse.FinesseSession(finesse_case_path, mode=mode)
boundary = finesse.FinesseInput.read_boundary_file(finesse_case_path + "files/boundary.dat")
np.seterr(all="ignore")
npoint = 33
#init_Q_poly = np.flipud([20,-68, -1.21, 55, -22, 0.001])
#init_P_poly = np.flipud([1.00 , -5.33 ,  17.52, -32.5 ,  30.00  , -11])
"""
input = {"Q_finesse_poly": copy.deepcopy(init_Q_poly),
     "P_finesse_poly": copy.deepcopy(init_P_poly),
     "A_N": [0.8, 26, 0.4],
     "gamma": 1.66666666666667,
     "alpha": 3,
     "epsilon": 0.3145,
     "NR": npoint,
     "NP": npoint,
     "NR_INVERSE": npoint,
     "NP_INVERSE": npoint,
     "boundary": np.array([[2.4402, 0], [-0.028406, 0.04322], [-0.27095, -0.051646], [0.047307, -0.034382], [0.064646, 0.03111], [-0.031225, 0.016667], [-0.019765, -0.021119], [0.018965, -0.0057205], [0.0049705, 0.013793], [-0.011547, 0.00040261], [0.0001408, -0.0084814], [0.0065918, 0.0017395], [-0.0020104, 0.0048597], [-0.0037037, -0.0023082], [0.0021292, -0.0025368], [0.001671, 0.0021344], [-0.0019914, 0.0010979], [-0.00071768, -0.0017109], [0.001379, -0.00029246], [-3.4953e-05, 0.001219], [-0.0010762, -0.00014045], [0.00016885, -0.00080944], [0.00054966, 0.0003023], [-0.00041285, 0.00046482], [-0.00041679, -0.00035115], [0.00025769, -0.0002443], [7.7295e-05, 0.00029995], [-0.00034897, 7.524e-05], [-0.00010391, -0.00024837], [0.0001322, -1.0763e-06], [-0.00010578, 0.00016165], [-0.00020879, -6.0143e-05], [-8.3546e-06, -0.00011623]]),
     "SIGN_I": -1
    }
"""
input = finesse.FinesseInput.read_input_file(finesse_case_path + "files/finesse_backup.inp")    
init_Q_poly = copy.deepcopy(input["Q_finesse_poly"])
init_P_poly = copy.deepcopy(input["P_finesse_poly"])
target = asdex.AsdexDataSet.load_matlab(finesse_case_path + "files/test_eq_AUG30382at2p5.mat")    
finesse_input = finesse.FinesseInput(input, boundary, target.a_0, target.B_phi0)

finesse_output = session.run_finesse(finesse_input)
estimation_case = finesse_output.assume_dp_dF_correct()
q_est, I_encl, (B_theta_est, B_phi_est) = estimation_case.estimate_q(finesse_input, mode="full")

q_error = tools.relative_error(finesse_output.q_finesse[0,:], q_est)
avg_q_error = np.nanmean(q_error)
print avg_q_error

trials = [("Q_finesse_poly", 1),
          ("Q_finesse_poly", 2),
          ("Q_finesse_poly", 3),
          ("Q_finesse_poly", 4),
          ("Q_finesse_poly", 5),
          ("P_finesse_poly", 1),
          ("P_finesse_poly", 2),
          ("P_finesse_poly", 3),
          ("P_finesse_poly", 4),
          ("P_finesse_poly", 5)]
trials = [("Q_finesse_poly", 1)]
poly_ranges = {"Q_finesse_poly": np.arange(-30, 30,1, dtype=float),
               "P_finesse_poly": np.linspace(-1, 1, num = 23, dtype=float)}
poly_ranges = {"Q_finesse_poly": np.arange(-30, 30,1, dtype=float)}
result = collections.OrderedDict()
#mode = "const"
#mode = "var"
mode = "shape"
for trial in trials:
    
    finesse_input.Q_finesse_poly = np.poly1d(copy.deepcopy(init_Q_poly))
    finesse_input.P_finesse_poly = np.poly1d(copy.deepcopy(init_P_poly))
    #result.append({"initial_input": copy.deepcopy(finesse_input),
     #              "poly": key})
    result[trial] = {}
    result[trial]["initial_input"] = copy.deepcopy(finesse_input)
    poly_range = poly_ranges[trial[0]]
    results_shape = collections.OrderedDict()
    for value in poly_range:
        init_poly = getattr(result[trial]["initial_input"], trial[0])
        poly = getattr(finesse_input, trial[0])        
        if mode == "var" or mode == "shape":
            poly[trial[1]] = init_poly[trial[1]] + value
            print poly
            setattr(finesse_input, trial[0], poly)
        try:    
            finesse_output = session.run_finesse(finesse_input)
        except finesse.FinesseSession.FinesseOutputError:
            result_shape = (np.nan, np.nan)
        results_shape[value] = (finesse_output.x_finesse, finesse_output.y_finesse)
    result[trial]["results_shape"] = results_shape
output = open('shape.pkl', 'wb')
pickle.dump(result, output)
output.close()


# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 12:50:34 2015

@author: karel
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
sys.path.append("/Users/karel/FORT/FINESSE/PF2q")
import pf2q.finesse as finesse
import matplotlib.pyplot as plt
import pickle

pkl_file = open('data_npoints.pkl', 'rb')
results = pickle.load(pkl_file)
pkl_file.close()
finesse_output = results[33]["finesse_output"]

a_0 = finesse_output.a_0
X_finesse = a_0 * finesse_output.x_finesse
Z_finesse = a_0 * finesse_output.y_finesse

boundary = finesse.FinesseInput.read_boundary_file("/Users/karel/FORT/FINESSE/finesse_/test_karel/INPUT/boundary.dat")
theta = np.linspace(0,2*np.pi,100)
sum_result = np.empty(theta.shape, dtype=complex)
for i, dtheta in enumerate(theta):
    sum_result[i] = np.sum([np.complex(row[0], row[1]) * np.exp(np.complex(0,(m+1)*dtheta)) for m, row in enumerate(boundary[1:,:])])
r = a_0 * (boundary[0,0]/2 + np.real(sum_result))
R0 = 2
X = r * np.cos(theta)
Z = -r * np.sin(theta)

plt.plot(X,Z)
plt.plot(X_finesse[:,-1],Z_finesse[:,-1])
plt.ylim([-1.5,1.5])
plt.xlim([-1.5,1.5])
plt.show()
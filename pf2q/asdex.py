#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains the tools needed to load and manipulate ASDEX-UPGRADE
data sets
@author: Karel van de Plassche
@licence: GPLv3
"""

import numpy as np
from scipy.interpolate import interp1d
import scipy.io as sio


class AsdexDataSet():
    """
    This class can be used to store data from ASDEX-UPGRADE. It expects
    the profiles p(rho), q(rho), rho, and rho(psi) and the constants a:=a_0,
    B_phi,0, and I_psi1.
    """
    profiles = ["p_of_rho_lin", "q_of_rho_lin", "rho_lin", "rho_of_psi"]
    constants = ["a_0", "B_phi0", "I_psi1"]

    def __init__(self, dict):
        """
        Initialize the AsdexDataSet with a dictionairy containing all profiles
        and constants.

        Arguments:
        dict -- dictionairy containing all profiles and constants.
        """
        for name in self.constants + self.profiles:
            try:
                setattr(self, name, dict[name])
            except KeyError:
                raise Exception("Please supply " + name)

    def convert_rho_to_psi(self, psi, rho):
        """
        Convert q(rho) to q(psi) for a given psi(rho).

        Arguments:
        psi -- the psi(rho) q will be mapped to
        rho -- the rho in psi(rho)

        Returns:
        q -- q(rho)
        """
        fq_of_rho_lin_vs_rho = interp1d(self.rho_lin,
                                        self.q_of_rho_lin, kind='cubic')
        frho_vs_psi = interp1d(psi, rho, kind='cubic')
        rho_vs_psi = frho_vs_psi(psi)
        rho_vs_psi[0] = 0
        rho_vs_psi[-1] = 1
        q = fq_of_rho_lin_vs_rho(rho_vs_psi)
        return q

    @staticmethod
    def load_matlab(path,
                    p_of_rho_lin_name="PTOT_profile_interp_ini",
                    q_of_rho_lin_name="Q_profile_interp_ini",
                    rho_of_psi_name="rho_tor_scale",
                    B_phi0_name="Bphi0",
                    a_0_name="a0",
                    I_psi1_name="Iaxis"):
        """
        Load a MATLAB file containing all profiles and constants needed to
        initialize this class. This function needs a map from the internal
        names of the variables to the names used in the MATLAB file. This
        map defaults to the standard used by F. Jaulmes at DIFFER.

        Arguments:
        path -- path to the MATLAB file

        Keyword Arguments:
        p_of_rho_lin_name -- The name of p(rho) in the MATLAB file
        q_of_rho_lin_name -- The name of q(rho) in the MATLAB file
        rho_of_psi_name -- The name of rho(psi) in the MATLAB file
        B_phi0_name -- The name of B_phi0 in the MATLAB file
        a_0_name -- The name of a_0 in the MATLAB file
        I_psi1_name -- The name of I_psi1 in the MATLAB file

        Returns:
        AsdexDataSet(dict) -- An instance of the AsdexDataSet class initialized
                              with the values from the MATLAB file
        """
        mat_contents = sio.loadmat(path)
        dict = {}
        dict["p_of_rho_lin"] = np.squeeze(mat_contents[p_of_rho_lin_name])
        dict["q_of_rho_lin"] = np.squeeze(mat_contents[q_of_rho_lin_name])
        dict["rho_of_psi"] = np.squeeze(mat_contents[rho_of_psi_name])
        dict["rho_lin"] = np.linspace(0, 1, num=len(dict["q_of_rho_lin"]))
        dict["B_phi0"] = np.squeeze(mat_contents[B_phi0_name])
        dict["a_0"] = np.squeeze(mat_contents[a_0_name])
        dict["I_psi1"] = np.squeeze(mat_contents[I_psi1_name])
        return AsdexDataSet(dict)

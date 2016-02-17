#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains tools to run FINESSE, load and save in- and output files
as well as functions to estimate q-profiles.
@author: Karel van de Plassche
@licence: GPLv3
"""

import collections
import re
import os
import subprocess
import posixpath
from itertools import chain
try:
    # for Python2
    import Tkinter as tk   ## notice capitalized T in Tkinter
    import tkFileDialog
except ImportError:
    # for Python3
    import tkinter as tk  ## notice here too
    from tkinter import filedialog as tkFileDialog


import numpy as np

import pf2q.tools as tools
import pf2q.fem as fem



np.seterr(all="ignore")

mu0 = 4 * np.pi * 10 ** -7


def calculate_beta(triangular_map, p, B_phi, R0):
    """ Calculate beta using FEM triangles

    Arguments:
    triangular_map -- map of the FEM triangles. See FEM module.
    p -- pressure in Pascal
    B_phi -- B_phi in Tesla
    R0 -- major radius in meter

    Returns:
    beta -- beta
    """

    (int_int_p_dV, volume), __ = triangular_map.volume_integral(
                                                np.tile(p, (p.size, 1)),
                                                R0)
    (int_int_B_phi2_dV, _), __ = triangular_map.volume_integral(
                                                B_phi ** 2,
                                                R0)
    beta = 2 * mu0 * int_int_p_dV / (int_int_B_phi2_dV)
    return beta


def calculate_betap(triangular_map, p, B_p, R0):
    """ Calculate beta poloidal using FEM triangles


    Arguments:
    triangular_map -- map of the FEM triangles. See FEM module.
    p -- pressure in Pascal
    B_p -- B_p in Tesla
    R0 -- major radius in meter

    Returns:
    beta_p -- beta poloidal
    """
    (int_int_p_dV, volume), __ = triangular_map.volume_integral(
                                                np.tile(p, (p.size, 1)),
                                                R0)
    (int_int_B_p2_dV, _), __ = triangular_map.volume_integral(
                                                B_p ** 2,
                                                R0)
    beta_p = 2 * mu0 * int_int_p_dV / (int_int_B_p2_dV)
    return beta_p


class FinesseDataSet():
    """ FINESSE output
    Structure derived from the FINESSE output file.

    The class saves (itermediate) results to avoid recalculation and
    increase speed. It contains the following constants and 2d data sets,
    all derived from /main/misc/mfinesse2file.f90 line 406.

    Constants:
    EPSILON, ALPHA, GAMMA, xMA, yMA, rhoMAoverrho0, BMAoverB0, Beta,
    Betap, NR_INVERSE, NP_INVERSE

    Variables:
    x_finesse, y_finesse, P_finesse, BR_finesse, BZ_finesse, Bphi_finesse,
    Grav, psi_finesse, q_finesse
    """

    # We have the constants and the (2d) data:
    constants = {"EPSILON": 0,
                 "ALPHA": 1,
                 "GAMMA": 2,
                 "xMA": 3,
                 "yMA": 4,
                 "rhoMAoverrho0": 5,
                 "BMAoverB0": 6,
                 "Beta": 7,
                 "Betap": 8,
                 "NR_INVERSE": 9,
                 "NP_INVERSE": 10}
    # Sort the constants. This makes parsing the output file easier.
    constants = collections.OrderedDict(sorted(constants.items(),
                                               key=lambda t: t[1]))
    # Parse data based on /main/misc/mfinesse2file.f90 line 406
    # There are 40 variables, we only need a few of them.
    data = {"x_finesse": 0,
            "y_finesse": 1,
            "P_finesse": 8,
            "BR_finesse": 14,
            "BZ_finesse": 20,
            "Bphi_finesse": 26,
            "Grav": 32,
            "psi_finesse": 38,
            "q_finesse": 39}
    data = collections.OrderedDict(sorted(data.items(),
                                           key=lambda t: t[1]))
    def __init__(self, dict, a_0, B_phi0):
        """
        Initialize with a dict containing the constants and 2d data sets. Also
        supply the tokamak constants a == a_0 and B_phi0.

        Arguments:
        dict -- dictionairy containing all constants and 2d data sets.
        a_0 -- the a_0 tokomak constant
        B_phi0 -- the B_phi0 tokomak constant
        """
        for name in chain(self.constants.keys(), self.data.keys()):
            try:
                setattr(self, name, dict[name])
            except KeyError:
                raise self.FinesseInputError("Please supply " + name)
        self.a_0 = a_0
        self.B_phi0 = B_phi0
        # Save some common geometric variables.
        self.R0 = None
        self.R = None
        self.x_map = None
        self.triangular_map = None

        # Save some common physical variables.
        self.B_phi = None
        self.B_p = None
        self.p = None
        self.rho = None

    def __str__(self):
        output_str = ""
        for constant in self.constants:
            output_str += constant + "=" + str(getattr(self, constant)) + ", "
        output_str += "\n"
        for matrix in self.data:
            output_str += matrix + "=..\n" + str(getattr(self, matrix)) + "\n"
        return output_str

    def calculate_rho(self):
        """ Calculate rho by integration of B_phi
        Calculate rho by integrating B_phi to get Phi := iint(B_phi dA)
        and rho := sqrt(Phi/Phi_1)

        Saves:
        rho -- rho
        triangular_map -- the triangulation of x_map
        common_geometric_constants -- see function
        common_physical_constants -- see function

        Returns:
        self.rho -- rho
        """
        if self.triangular_map is None:
            if self.x_map is None:
                self.calculate_common_geometric_constants()
            self.triangular_map = self.x_map.triangulate()
        if self.B_phi is None:
            self.calculate_common_physical_constants()

        # Reconstruct rho
        Phi = self.triangular_map.ring_integral(self.B_phi)
        rho = np.sqrt(abs(Phi/max(abs(Phi))))
        self.rho = np.insert(rho, 0, 0)
        return self.rho

    def calculate_p(self, B_p_est, B_phi_est):
        """ Calculate physical pressure with the beta method
        Calculate beta and beta poloidal using the estimation of magnatic
        fields and compare it with the betas from FINESSE output.

        Arguments:
        B_p_est -- estimation of B_p
        B_phi_est -- estimation of B_phi

        Saves:
        p -- physical pressure in Pa
        triangular_map -- the triangulation of x_map
        common_geometric_constants -- see function
        common_physical_constants -- see function

        Returns:
        self.p -- physical pressure in Pa
        """
        if self.triangular_map is None:
            if self.x_map is None:
                self.calculate_common_geometric_constants()
            self.triangular_map = self.x_map.triangulate()
        if self.B_p is None or self.B_phi is None:
            self.calculate_common_physical_constants()

        # p is an flux constant
        p_output = self.P_finesse[0, :]
        beta_est = calculate_beta(self.triangular_map, p_output, B_phi_est,
                                  self.a_0 / self.EPSILON)
        betap_est = calculate_betap(self.triangular_map, p_output, B_p_est,
                                    self.a_0 / self.EPSILON)

        coof_P_finesse = np.average((self.Beta / beta_est,
                                     self.Betap / betap_est))
        self.p = coof_P_finesse * p_output
        return self.p

    def calculate_common_geometric_constants(self):
        """ Calculate common geometric constants
        Rescale x_tilde and y_tilde from FINESSE to their physical value in
        meter using a_0, calculate R0 and calculate R:= R0 + x

        Saves:
        R0 -- major radius in meters
        x_map -- the (x, y) map in meters. See FEM module
        R -- major coordinate in meters
        """
        if self.R0 is None:
            self.R0 = self.a_0 / self.EPSILON
        if self.x_map is None:
            self.x_map = fem.Map(self.a_0 * self.x_finesse,
                                 self.a_0 * self.y_finesse,
                                 (self.a_0 * self.xMA, self.a_0 * self.yMA))
        if self.R is None:
            self.R = self.R0 + self.x_map.points_x[:, :, 0]

    def calculate_common_physical_constants(self):
        """ Calculate common physical constants
        Rescale B_phi from FINESSE back using B_phi0, calculate B_p from
        B_R and B_Z from FINESSE
        Use that B_phi:=B_phi0 * B_phi_tilde, B_p:=B_phi0 * B_p_tilde and
        B_p = sqrt(B_R^2 + B_Z^2)

        Saves:
        B_phi -- B_phi in Tesla
        B_p -- B_p in Tesla
        """
        if self.B_phi is None:
            self.B_phi = self.B_phi0 * self.Bphi_finesse
        if self.B_p is None:
            self.B_p = (self.B_phi0 *
                        np.sqrt(self.BR_finesse ** 2 +
                                self.BZ_finesse ** 2))

    def estimate_from_output(self):
        """ Estimate q-profile using only output
        Estimates the q-profile using the B_phi and B_p of the output file.
        This should give a nearly exact match.

        Returns:
        abs(q) -- the absolute value of the q-profile
        """
        # These are constants
        self.calculate_common_geometric_constants()
        self.calculate_common_physical_constants()
        self.x_map.calculate_poloidal()

        # Estime q by doing q = \int(B_phi dl / (R B_p))
        (q, _) = self.x_map.contour_integral(self.B_phi[0:-1, :] /
                                             (self.R[0:-1, :] *
                                              self.B_p[0:-1, :]))
        q /= 2 * np.pi

        # We are only interested in the magnitude of q, so:
        return abs(q)

    def assume_dp_dF_correct(self):
        """ Calculate dF and dp assuming they are correct in the output
        Calculate the physical difference in F- and p-profile. F is
        reconstructed using F:= R B_phi and p is reconstructed using the
        beta method.

        Returns:
        estimate_case an instance of EstimationCase
        """
        if self.B_p is None or self.B_phi is None:
            self.calculate_common_physical_constants()
        p = self.calculate_p(self.B_p, self.B_phi)
        P_0 = p[0]
        P_1 = p[-1]
        F_0 = (self.R * self.B_phi)[0, 0]
        F_1 = (self.R * self.B_phi)[0, -1]

        # And find out how B_p scales
        B_p_int, dl = self.x_map.contour_integral(self.B_p[:-1, :])
        L = np.sum(dl, axis=0)
        B_p_int /= L
        B_p_int[L == 0] = 0
        B_p_int = np.tile(B_p_int, (B_p_int.size, 1))
        scaling = self.B_p/B_p_int
        scaling[B_p_int == 0] = 1

        estimate_case = EstimationCase((self, scaling),
                                       P_0, P_1, F_0, F_1)
        return estimate_case


class FinessePaths():
    def __init__(self,
                 finesse_case_path,
                 rel_output_path="OUTPUT/",
                 rel_input_path="INPUT/",
                 rel_data_path="DATA/",
                 path_module=posixpath):
        """
        Specifies all the paths in the (remote) FINESSE distribution.

        Arguments:
        finesse_case_path -- the path of the FINESSE case for this session

        Keyword arguments:
        rel_output_path -- FINESSE OUTPUT path relative to finesse_case_path
        rel_input_path -- FINESSE INPUT path relative to finesse_case_path
        rel_data_path -- FINESSE DATA path relative to finesse_case_path
        """
        self.OUTPUT_path = path_module.join(finesse_case_path, rel_output_path)
        self.INPUT_path = path_module.join(finesse_case_path, rel_input_path)
        self.DATA_path = path_module.join(finesse_case_path, rel_data_path)
        self.finesse_case_path = finesse_case_path
        self.path_module = path_module


def make_run_finesse_remote(send_input_boundary, run_finesse,
                            copy_remote_ouput, remove_remote):
    """
    Provides the skeleton of how to run a script locally and FINESSE
    remotely. send_input_boundary should be a function that sends the
    input file and boundary file to the remote server, run_finesse
    should run FINESSE remotely, copy_remote_ouput should copy the remotely
    generated .dat file to the local client, and remove_remote should
    remove any remotely generated files.
    """
    def run_finesse_remote(input_data, result_path):
        try:
            send_input_boundary(input_data)
        except subprocess.CalledProcessError:
            error_msg = "Could not copy local to remote"
            FinesseSession.FinesseOutputError(error_msg)
        try:
            run_finesse()
        except subprocess.CalledProcessError:
            error_msg = "Could not run FINESSE"
            raise FinesseSession.FinesseOutputError(error_msg)
        try:
            copy_remote_ouput(result_path)
        except subprocess.CalledProcessError:
            error_msg = "Could not copy remote to local, did FINESSE converge?"
            raise FinesseSession.FinesseOutputError(error_msg)
        try:
            remove_remote()
        except subprocess.CalledProcessError:
            error_msg = "Could not remove remote data, log or input"
            raise FinesseSession.FinesseOutputError(error_msg)
    return run_finesse_remote


class FinesseSession():
    """ Specifies the FINESSE case
    This class defines all the paths needed to run FINESSE and contains
    functions to run FINESSE and import its output.
    """

    def __init__(self, finesse_paths, run_finesse_function, result_path):
        """
        The FINESSE session needs a function that specifies how FINESSE
        should be run. This function should do at least the following things
        on the machine that runs FINESSE: save the finesse.inp in INPUT_path,
        save boundary.dat in DATA_path, run FINESSE, and copy the resulting
        .dat file to the result_path on the machine running PF2q.
        Optionally the generated .log file can be deleted too. You can use
        any of the supplied example functions in the unix/windows_function
        modules class or create your own. You can also use the
        make_run_finesse_remote as skeleton.

        Arguments:
        finesse_case_path -- the path of the FINESSE case for this session
        run_finesse_function -- function used to run FINESSE
        result_path -- path where the result of run_finesse_function is stored
        """
        self.finesse_paths = finesse_paths
        self.run_finesse_function = run_finesse_function
        self.result_path = result_path

    def run_finesse(self, input_data, backup_result=False):
        """ Run finesse locally or remotely
        This function saves the ouput to the result_path and either deletes it
        or optionally renames it with .backup at the end.

        Arguments:
        input_data -- an instance of FinesseInput, specifies the input file

        Keyword Arguments:
        backup_result -- If true, backs up the result, otherwise deletes it
        Returns:
        finesse_data -- instance of FinesseDataSet read from FINESSE output
        """
        # Be sure that there are no old .dat files in result_path
        #try:
        for file in os.listdir(self.result_path):
            abs_path = os.path.join(self.result_path, file)
            if file.startswith("finesse"):
                if file.endswith(".dat") or file.endswith(".dat.lnk"):
                    error_msg = "Old .dat file found. Please clear result_path"
                    raise FinesseSession.FinesseOutputError(error_msg)
        #except FinesseSession.FinesseOutputError:
        #    finesse_data = None
        #    print(error_msg)
        #else:
        self.run_finesse_function(input_data, self.result_path)

        # Read and save the output data
        worked = False
        for file in os.listdir(self.result_path):
           abs_path = os.path.join(self.result_path, file)
           if file.startswith("finesse"):
               if file.endswith(".dat") or file.endswith(".dat.lnk"):
                   finesse_data = FinesseSession.read_output_data(abs_path)
                   worked = True
               if backup_result:
                   os.rename(abs_path, abs_path + ".backup")
               else:
                   os.remove(abs_path)

        if not worked:
           error_msg = "Could not find output file. Did FINESSE converge?"
           raise FinesseSession.FinesseOutputError(error_msg)

        finesse_data = FinesseDataSet(finesse_data, input_data.a_0,
                                     input_data.B_phi0)
        return finesse_data

    @classmethod
    def read_output_data(self, file_path):
        """ Read the Finesse file and parse data
        Arguments:
        file_path -- path of FINESSE output file (ending in .dat or .dat.lnk)

        Returns:
        finesse_data -- instance of FinesseDataSet read from FINESSE output
        """

        with open(file_path, 'r') as f:
            line = f.readline()
            words = re.split(r'\s{1,}', line)
            values = [float(word)for word in words[1:-1]]
            finesse_data = dict(zip(FinesseDataSet.constants, values))

            line = f.readline()
            words = re.split(r'\s{1,}', line)
            finesse_data["NR_INVERSE"] = int(words[1])
            finesse_data["NP_INVERSE"] = int(words[2])
            matrix = np.empty([finesse_data["NR_INVERSE"] *
                               finesse_data["NP_INVERSE"], 40], dtype=float)
            for i, line in enumerate(f):
                words = re.split(r'\s{1,}', line)
                values = [float(word)for word in words[1:-1]]
                matrix[i] = values
            d3_matrix = np.reshape(matrix, [finesse_data["NR_INVERSE"],
                                            finesse_data["NP_INVERSE"], 40])
            for column_name, column_number in FinesseDataSet.data.items():
                finesse_data[column_name] = d3_matrix[:, :, column_number]

        return finesse_data

    @staticmethod
    class FinesseOutputError(Exception):
        def __init__(self, message):
            super(FinesseSession.FinesseOutputError, self).__init__(message)


class FinesseInput:
    """ Specifies the FINESSE input.
    It contains the following elements:

    Constants:
    "A_N", "gamma", "alpha", "epsilon", "NR", "NP", "NR_INVERSE", "NP_INVERSE"

    Profiles:
    "F2_tilde_poly", "P_tilde_poly"
    """
    profiles = ["F2_tilde_poly", "P_tilde_poly"]
    constants = ["A_N", "gamma", "alpha", "epsilon",
                 "NR", "NP", "NR_INVERSE", "NP_INVERSE",
                 "SIGN_I"]

    def __init__(self, dict, boundary, a_0, B_phi0):
        """ FINESSE input
        Structure derived from the FINESSE input file. Initialize with a dict
        containing the elements of FinesseInput
        """
        for constant in self.constants:
            try:
                setattr(self, constant, dict[constant])
            except KeyError:
                raise self.FinesseInputError("Please supply " + constant)
        for profile in self.profiles:
            try:
                setattr(self, profile, np.poly1d(dict[profile]))
            except KeyError:
                raise self.FinesseInputError("Please supply " + profile)

        self.boundary = boundary
        self.a_0 = a_0
        self.B_phi0 = B_phi0

    @classmethod
    def read_input_file(self, path):
        finesse_input_dict = {}
        reading_poly = False
        with open(path, 'r') as input:
            for line in input:
                line = line.replace(",", " ")
                words = line.split()
                if words[0] == "GAMMA":
                    finesse_input_dict["gamma"] = float(words[-1])
                elif words[0] == "ALPHA":
                    finesse_input_dict["alpha"] = float(words[-1])
                elif words[0] == "EPSILON":
                    finesse_input_dict["epsilon"] = float(words[-1])
                elif words[0] == "C":
                    reading_poly = True
                    poly = []
                    for i in range(10):
                        poly.append(float(words[-1 - i]))
                    finesse_input_dict["F2_tilde_poly"] = poly
                    n_poly = 1
                elif reading_poly:
                    if n_poly == 1:
                        poly = []
                        for i in range(10):
                            poly.append(float(words[-1 - i]))
                        finesse_input_dict["P_tilde_poly"] = poly
                        reading_poly = False
                elif words[0] == "A_N":
                    A_N = []
                    for i in range(6):
                        A_N.append(float(words[2 + i]))
                    finesse_input_dict["A_N"] = A_N
                elif words[0] == "SIGN_I":
                    finesse_input_dict["SIGN_I"] = float(words[-1])
                elif words[0] == "NR":
                    finesse_input_dict["NR"] = int(words[-1])
                elif words[0] == "NP":
                    finesse_input_dict["NP"] = int(words[-1])
                elif words[0] == "NR_INVERSE":
                    finesse_input_dict["NR_INVERSE"] = int(words[-1])
                elif words[0] == "NP_INVERSE":
                    finesse_input_dict["NP_INVERSE"] = int(words[-1])
                else:
                    pass
        return finesse_input_dict

    def input_to_file(self, save_name):
        """ Save the FinesseInput instance to an input file
        Structure derived from the FINESSE input file.

        Arguments:
        save_name -- path and name to save the resulting FINESSE input file
        """
        with open(save_name, 'w') as output:
            output.write(" &FINESSE_GLOBAL_PARAMETERS\n")
            output.write("    FINESSE_INPUT_FILE_VERSION = \"1.1\"\n")
            output.write("    ANNOTATION                 = \"ITER static\"\n")
            output.write(" /\n")
            output.write(" &FINESSE_IO_PARAMETERS\n")
            output.write("    FAST_DB_FILENAME = \"X.fbdb\"\n")
            output.write("    SLOW_DB_FILENAME = \"X.sbdb\"\n")
            output.write("    DATA_FILE        = .TRUE.\n")
            output.write("    DX_FILE          = .FALSE.\n")
            output.write("    HAGIS_FILE       = .FALSE.\n")
            output.write("    PHOENIX_FILE     = .FALSE.\n")
            output.write("    POSTSCRIPT_FILE  = .FALSE.\n")
            output.write("    VAC_FILE         = .FALSE.\n")
            output.write("    VTK_FILE         = .FALSE.\n")
            output.write(" /\n")
            output.write(" &FINESSE_MODE_PARAMETERS\n")
            output.write("    MODE                      = \"static\"\n")
            output.write("    APPLICATION               = \"tokamak\"\n")
            output.write("    BERNOULLI_SOLUTION_METHOD = \"root-finding\"\n")
            output.write(" /\n")
            output.write(" &FINESSE_PHYSICS_PARAMETERS\n")
            output.write("    GAMMA = " + str(self.gamma) + "\n")
            output.write(" /\n")
            output.write(" &FINESSE_PROFILE_PARAMETERS\n")

            output.write("    C = " + str(self.F2_tilde_poly[0]))
            for i in range(1, 10):
                try:
                    output.write(", " + str(self.F2_tilde_poly[i]))
                except IndexError:
                    output.write(", 0.0")
            output.write("\n")
            output.write("        " + str(self.P_tilde_poly[0]))
            for i in range(1, 10):
                try:
                    output.write(", " + str(self.P_tilde_poly[i]))
                except IndexError:
                    output.write(", 0.0")
            output.write("\n")
            output.write("        1.0, -0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n")
            output.write("        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n")
            output.write("        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n")
            output.write("        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n")
            output.write("    A_N = " + str(self.A_N[0]))
            for i in range(1, 6):
                try:
                    output.write(", " + str(self.A_N[i]))
                except IndexError:
                    output.write(", 0.0")
            output.write("\n")
            output.write("    SIGN_CHI_PRIME = +1.\n")
            output.write("    SIGN_OMEGA     = +1.\n")
            if self.SIGN_I == 1:
                output.write("    SIGN_I         = +1.\n")
            elif self.SIGN_I == -1:
                output.write("    SIGN_I         = -1.\n")
            else:
                self.FinesseInputError(" SIGN_I can only be -1 or +1, not" +
                                       self.SIGN_I)
            output.write(" /\n")
            output.write(" &FINESSE_FLUX_PARAMETERS\n")
            output.write("    ALPHA               = " + str(self.alpha) + "\n")
            output.write("    AVERAGE_FLUXPROFILE = \"none\"\n")
            output.write("    FLUXFUNCTION        = \"temperature\"\n")
            output.write("    FLUXPROFILES        = \"primitive\"\n")
            output.write(" /2.2\n")
            output.write(" &FINESSE_DELTA_PARAMETERS\n")
            output.write("    DELTAPROFILES      = \"polynomial\",\"polynomial\",\"polynomial\",\"polynomial\",\"polynomial\",\"polynomial\"\n")
            output.write("     INTERPOLATION_TYPE = \"cubic\"\n")
            output.write(" /\n")
            output.write(" &FINESSE_GEOMETRY_PARAMETERS\n")
            output.write("    EPSILON            = " + str(self.epsilon) + "\n")
            output.write("    TOP_DOWN_SYMMETRIC = .FALSE.\n")
            output.write("    RZ_NORMALIZATION   = \"tokamak\"\n")
            output.write(" /\n")
            output.write(" &FINESSE_SHAPE_PARAMETERS\n")
            output.write("    CS_SHAPE = \"data\"\n")
            output.write("    NM       = 64\n")
            output.write("    ELLIPS   = 1.7\n")
            output.write("    TRIANG   = 0.4\n")
            output.write("    QUADRA   = 0.0\n")
            output.write(" /\n")
            output.write(" &FINESSE_BC_PARAMETERS\n")
            output.write("    BC_TYPE = \"none\",\"essential\",\"periodic\",\"periodic\"\n")
            output.write(" /\n")
            output.write(" &FINESSE_GRID_PARAMETERS\n")
            output.write("     NR                 =  " + str(self.NR) + "\n")
            output.write("     NP                 =  " + str(self.NP) + "\n")
            output.write("    INVERSECOORDINATES = .TRUE.\n")
            output.write("    STRAIGHTFIELDLINES = .TRUE.\n")
            output.write("     NR_INVERSE         =  " + str(self.NR_INVERSE) + "\n")
            output.write("    NP_INVERSE         =  " + str(self.NP_INVERSE) + "\n")
            output.write("    GRID_TYPE          = \"linear\",\"linear\"\n")
            output.write(" /\n")
            output.write(" &FINESSE_FLOW_DOMAIN_PARAMETERS\n")
            output.write("    FLOW_DOMAIN = \"sub-slow\"\n")
            output.write(" /\n")
            output.write(" &FINESSE_DEBUG_PARAMETERS\n")
            output.write("    DEBUG_MROOT               = .FALSE.\n")
            output.write("    DEBUG_MDOMAIN             = .FALSE.\n")
            output.write("    DEBUG_MUPDATEM2           = .FALSE.\n")
            output.write("    DEBUG_MINVERSECOORDINATES = .FALSE.\n")
            output.write("    DEBUG_MSTRAIGHTFIELDLINES = .FALSE.\n")
            output.write(" /\n")

    def boundary_to_file(self, absolute_path):
        """ Save the FinesseInput boundary to a boundary file

        Arguments:
        absolute_path -- path and name to save the resulting boundary file to
        """
        # Save the boundary file
        with open(absolute_path, 'w') as output:
            output.write(str(self.boundary.shape[0]) + "\n")
            for row in self.boundary:
                output.write(str(row[0]) + " " + str(row[1]) + "\n")

    @classmethod
    def read_boundary_file(self, absolute_path):
        """ Read a boundary file to a boundary for the FinesseInput

        Arguments:
        absolute_path -- path and name to load the resulting boundary file from
        """
        boundary = np.empty([0, 2])
        with open(absolute_path, 'r') as input:
            for i, line in enumerate(input):
                if i > 0:
                    line = line.replace(",", " ")
                    words = line.split()
                    boundary = np.vstack((boundary,
                                          [float(words[0]),
                                           float(words[1])]))
        return boundary

    def save_input_dialog(self, initialdir=None):
        root = tk.Tk()
        root.withdraw()
        file_name = tkFileDialog.asksaveasfilename(initialdir=initialdir)
        if file_name != '':
            self.input_to_file(file_name)
        else:
            raise self.FinesseInputError("No file selected")

    def load_input_dialog(self, initialdir=None):
        root = tk.Tk()
        root.withdraw()
        file_name = tkFileDialog.askopenfilename(initialdir=initialdir)
        if file_name != '':
            return FinesseInput.read_input_file(file_name)
        else:
            raise self.FinesseInputError("No file selected")

    class FinesseInputError(Exception):
        def __init__(self, message):
            super(FinesseInput.FinesseInputError, self).__init__(message)


class EstimationCase():
    """ Specifies an estimation case
    This is a convinience class that links together a FINESSE output file
    (or more precicely a FinesseDataSet instance) and variables that
    can not (easily) be derived from the output, namely:

    - core pressure in Pascal
    - edge pressure in Pascal
    - core physical F
    - edge physical F
    - Shape of B_p on a flux surface
    An estimation of these parameters can be made with
    FinesseDataSet.assume_dp_dF_correct()
    """
    def __init__(self, finesse_output_B_p_scaling, P_0, P_1, F_0, F_1):
        """
        Arguments:
        (finesse_output, B_p_scaling) -- a tuple with:
            finesse_output -- a FinesseDataSet instance
            B_p_scaling -- the scaling of B_p on a flux surface
        P_0 -- core pressure in Pascal
        P_1 -- edge pressure in Pascal
        F_0 -- core physical F
        F_1 -- edge physical F
        """
        self.finesse_output, self.B_p_scaling= finesse_output_B_p_scaling
        self.P_0 = P_0
        self.P_1 = P_1
        self.F_0 = F_0
        self.F_1 = F_1
        self.Psi_1 = ((self.finesse_output.a_0 ** 2 * self.finesse_output.B_phi0) /
                      (self.finesse_output.BMAoverB0 * self.finesse_output.ALPHA))

    def estimate_q(self, finesse_input):
        """ Estimate q-profile from FINESSE input file

        Arguments:
        finesse_input -- a FIN         = B_p_scalingESSE input file (or more precicely a
                         FinesseInput instance)

        Returns:
        abs(q_est), I_encl, (B_p_est, B_phi_est)
        q_est -- estimated q-profile
        I_encl -- enclosed current in Ampere by flux-surface
        (B_p_est, B_phi_est) -- estimated magnetic fields
        """

        # This is just to prevent typing self. everywhere
        (finesse_output, B_p_scaling), P_0, P_1, F_0, F_1 = \
           (self.finesse_output, self.B_p_scaling), \
            self.P_0, self.P_1, self.F_0, self.F_1

        F2_tilde = np.polyval(finesse_input.F2_tilde_poly,
                              finesse_output.psi_finesse[0, :])
        F2, (c_F, _) = tools.rescale(F2_tilde, F_0 ** 2, F_1 ** 2)

        P = np.polyval(finesse_input.P_tilde_poly,
                       finesse_output.psi_finesse[0, :])
        _, (c_p, _) = tools.rescale(P, P_0, P_1)

        # Use dx/dPsi = dx/dx_finesse * dx_finesse/dpsi * dpsi/dPsi
        # with dx/dx_finesse = c_x and dpsi/dPsi = 1/Psi_1
        F2_poly = finesse_input.F2_tilde_poly.deriv() * c_F/self.Psi_1
        F2_prime = np.polyval(F2_poly, finesse_output.psi_finesse[0, :])
        p_poly = finesse_input.P_tilde_poly.deriv() * c_p/self.Psi_1
        p_prime = np.polyval(p_poly, finesse_output.psi_finesse[0, :])

        R0 = finesse_input.a_0 / finesse_input.epsilon
        R = R0 + finesse_output.x_map.points_x[:, :, 0]

        j_phi = -0.5 * F2_prime / (mu0 * R) - p_prime * R

        I_encl = finesse_output.triangular_map.ring_integral(j_phi)
        I_encl = np.insert(I_encl, 0, 0)
        dl = finesse_output.triangular_map.calculate_dl()
        L = np.sum(dl, axis=0)
        B_p_est_const = mu0 * I_encl / L
        B_p_est_const[0] = 0
        # This assumes B_p is constant over a flux surface
        B_p_est_const_c = np.tile(B_p_est_const, (len(B_p_est_const), 1))
        # We know that isn't true, so let's rescale according output
        B_p_est = B_p_scaling * B_p_est_const_c

        B_phi_est = finesse_input.SIGN_I * np.tile(np.sqrt(F2),
                                                   (len(F2), 1)) / R

        q_est, _ = finesse_output.x_map.contour_integral((B_phi_est /
                                                     (R * B_p_est))[0:-1, :])
        q_est /= 2 * np.pi
        q_est *= finesse_input.alpha / finesse_output.ALPHA

        return q_est, I_encl, (B_p_est, B_phi_est)

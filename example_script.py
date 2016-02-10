#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Karel van de Plassche
@licence: GPLv3
"""
import os
from sys import platform
import posixpath

import numpy as np
import matplotlib


import pf2q.asdex as asdex
import pf2q.finesse as finesse
import pf2q.windows_functions as windows_functions
import pf2q.unix_functions as unix_functions

if __name__ == '__main__':
    ###########################################################################
    # Initialize FinesseSession                                               #
    ###########################################################################
    # The script automatically tries to determine who is running it. You can
    # either add your own case or just create your own script.

    user = None
    mode = None
    if platform == "win32":
        if os.environ['COMPUTERNAME'] == "DESKTOP-KF2LUV7":
            user = "Karel"
            mode = "remote_windows"
        elif os.environ['COMPUTERNAME'] == "PCNPD1":
            user = "Fabien"
            mode = "differ_windows"
        elif os.environ['COMPUTERNAME'] == "PCNPD2":
            user = "Selwyn"
            mode = "differ_windows"
    elif platform == "darwin":
        user = "Karel"
        mode = "remote_mac"
    elif platform == "linux2":
        user = "Karel"
        mode = "local_linux"

    if user == "Karel":
        if mode == "remote_mac" or mode == "remote_windows":
            rel_finesse_case_path = "FORT/FINESSE/finesse_/test_karel/"
            home_folder = "/home/emc/plassche"
            finesse_case_path = posixpath.join(home_folder, rel_finesse_case_path)
            finesse_paths = finesse.FinessePaths(finesse_case_path)
            remote_user = "plassche"
            remote_gate = "gate.rijnhuizen.nl"
            remote_server = "rs1"
            if mode == "remote_mac":
                local_input_path = os.path.join("/Users","karel/Dropbox", "Internship/PF2q")
                local_output_path = "/Users/karel/Dropbox/Internship/PF2q"
                f1 = unix_functions.make_send_input_boundary(finesse_paths, remote_user, remote_gate)
                f2 = unix_functions.make_run_finesse_gate(finesse_paths, remote_user, remote_gate, remote_server)
                f3 = unix_functions.make_copy_remote_ouput(finesse_paths, remote_user, remote_gate)
                f4 = unix_functions.make_remove_remote(finesse_paths, remote_user, remote_gate)
                run_finesse_function = finesse.make_run_finesse_remote(f1, f2, f3, f4)
    
                # Fit nicely on the screen
                matplotlib.use('TkAgg')
                matplotlib.rcParams['font.size'] = 20
                matplotlib.rcParams["figure.dpi"] = 96
                matplotlib.rcParams["figure.figsize"] = [12.0, 9.0]  # In inch
    
            elif mode == "remote_windows":
                local_home_path = "D:\\"
                local_input_path = os.path.join(local_home_path, rel_finesse_case_path, "INPUT")
                local_data_path = os.path.join(local_home_path, rel_finesse_case_path, "DATA")
                local_output_path = os.path.join(local_home_path, rel_finesse_case_path, "OUTPUT")
    
                putty_path_base = "D:\Program Files (x86)\PuTTY"
                putty_path = os.path.join(putty_path_base, "putty.exe")
                pscp_path = os.path.join(putty_path_base, "pscp.exe")
                putty_session = "rijnhuizen_gate"
    
                f1 = windows_functions.make_send_input_boundary_pscp(finesse_paths, pscp_path, putty_session, remote_user, remote_gate)
                f2 = windows_functions.make_run_finesse_gate(finesse_paths, putty_path, putty_session, remote_user, remote_gate, remote_server)
                f3 = windows_functions.make_copy_remote_ouput(finesse_paths, pscp_path, putty_session, remote_user, remote_gate)
                f4 = windows_functions.make_remove_remote(finesse_paths, putty_path, putty_session, remote_user, remote_gate)
                run_finesse_function = finesse.make_run_finesse_remote(f1, f2, f3, f4)
    
                # Fit nicely on the screen
                matplotlib.rcParams['font.size'] = 20
                matplotlib.rcParams["figure.dpi"] = 96
                matplotlib.rcParams["figure.figsize"] = [20.0, 12.0]  # In inch
        elif mode == "local_linux":
            rel_finesse_case_path = "FORT/FINESSE/finesse_/test_karel/"
            home_folder = "/home/karel"
            finesse_case_path = os.path.join(home_folder, rel_finesse_case_path)
            finesse_paths = finesse.FinessePaths(finesse_case_path)
            local_output_path = finesse_paths.OUTPUT_path
            local_input_path = finesse_paths.INPUT_path
            run_finesse_function = unix_functions.make_run_finesse_local(finesse_paths)
            matplotlib.rcParams['font.size'] = 20
            matplotlib.rcParams["figure.dpi"] = 96
            matplotlib.rcParams["figure.figsize"] = [12.0, 9.0]  # In inch
            
    elif user == "Selwyn":
        rel_finesse_case_path = "FORT/FINESSE/finesse1/kareltest/"
        home_folder = "/home/emc/cats"
        finesse_case_path = posixpath.join(home_folder, rel_finesse_case_path)
        finesse_paths = finesse.FinessePaths(finesse_case_path)
        remote_user = "cats"
        remote_gate = "gate.rijnhuizen.nl"
        remote_server = "rs1"
        if mode == "differ_windows":
            local_home_path = "H:\\"
            local_input_path = os.path.join(local_home_path, rel_finesse_case_path, "INPUT")
            local_data_path = os.path.join(local_home_path, rel_finesse_case_path, "DATA")
            local_output_path = os.path.join(local_home_path, rel_finesse_case_path, "OUTPUT")

            putty_path_base = "C:\Program Files (x86)\PuTTY"
            putty_path = os.path.join(putty_path_base, "putty.exe")
            putty_session = "rs1"
            def empty(self):
                pass
            def empty2():
                pass
            f1 = windows_functions.make_save_input_boundary(local_input_path, local_data_path)
            f2 = windows_functions.make_run_finesse(finesse_paths, putty_path, putty_session, remote_user, remote_server)
            f3 = empty
            f4 = empty2
            run_finesse_function = finesse.make_run_finesse_remote(f1, f2, f3, f4)
            
    elif user == "Fabien":
        rel_finesse_case_path = "FORT/FINESSE/finesse~1/AUG_31557_2p25/"
        home_folder = "/home/emc/jaulmes"
        finesse_case_path = posixpath.join(home_folder, rel_finesse_case_path)
        finesse_paths = finesse.FinessePaths(finesse_case_path)
        remote_user = "jaulmes"
        remote_gate = "gate.rijnhuizen.nl"
        remote_server = "rs1"
        if mode == "differ_windows":
            local_home_path = "H:\\"
            local_input_path = os.path.join(local_home_path, rel_finesse_case_path, "INPUT")
            local_data_path = os.path.join(local_home_path, rel_finesse_case_path, "DATA")
            local_output_path = os.path.join(local_home_path, rel_finesse_case_path, "OUTPUT")

            putty_path_base = "C:\Program Files (x86)\PuTTY"
            putty_path = os.path.join(putty_path_base, "putty.exe")
            putty_session = "rs1.rijnhuizen.nl"
            def empty(self):
                pass
            def empty2():
                pass
            f1 = windows_functions.make_save_input_boundary(local_input_path, local_data_path)
            f2 = windows_functions.make_run_finesse(finesse_paths, putty_path, putty_session, remote_user, remote_server)
            f3 = empty
            f4 = empty2
            run_finesse_function = finesse.make_run_finesse_remote(f1, f2, f3, f4)
                
            matplotlib.rcParams['font.size'] = 22
            matplotlib.rcParams["figure.dpi"] = 96
            matplotlib.rcParams["figure.figsize"] = [20.0, 12.0]  # In inch
            
        elif mode == "remote_windows":
            local_home_path = "D:\\"
            local_input_path = os.path.join(local_home_path, rel_finesse_case_path, "INPUT")
            local_data_path = os.path.join(local_home_path, rel_finesse_case_path, "DATA")
            local_output_path = os.path.join(local_home_path, rel_finesse_case_path, "OUTPUT")

            putty_path_base = "D:\Program Files (x86)\PuTTY"
            putty_path = os.path.join(putty_path_base, "putty.exe")
            pscp_path = os.path.join(putty_path_base, "pscp.exe")
            putty_session = "rijnhuizen_gate"

            f1 = windows_functions.make_send_input_boundary_pscp(finesse_paths, pscp_path, putty_session, remote_user, remote_gate)
            f2 = windows_functions.make_run_finesse_gate(finesse_paths, putty_path, putty_session, remote_user, remote_gate, remote_server)
            f3 = windows_functions.make_copy_remote_ouput(finesse_paths, pscp_path, putty_session, remote_user, remote_gate)
            f4 = windows_functions.make_remove_remote(finesse_paths, putty_path, putty_session, remote_user, remote_gate)
            run_finesse_function = finesse.make_run_finesse_remote(f1, f2, f3, f4)

            
    session = finesse.FinesseSession(finesse_case_path, run_finesse_function, local_output_path)
    
    # Load modules that use matplotlib after the right backend has loaded
    import matplotlib.pyplot as plt
    import pf2q.pf2qvis as pf2qvis
    ###########################################################################
    # Define input parameters                                                 #
    ###########################################################################
    # Manually inside the script
    npoint = 33
    input = {"F2_tilde_poly": np.flipud([20, -68, -1.21, 55.25, -22, 0.001]),
             "P_tilde_poly": np.flipud([1.00, -5.33, 17.52, -32.5, 30.04, -10.72]),
             "A_N": [0.8, 26, 0.4],
             "gamma": 1.66666666666667,
             "alpha": 3,
             "epsilon": 0.3145,
             "NR": npoint,
             "NP": npoint,
             "NR_INVERSE": npoint,
             "NP_INVERSE": npoint,
             "SIGN_I": -1
             }
    boundary = np.array([[2.4402, 0], [-0.028406, 0.04322], [-0.27095, -0.051646], [0.047307, -0.034382], [0.064646, 0.03111], [-0.031225, 0.016667], [-0.019765, -0.021119], [0.018965, -0.0057205], [0.0049705, 0.013793], [-0.011547, 0.00040261], [0.0001408, -0.0084814], [0.0065918, 0.0017395], [-0.0020104, 0.0048597], [-0.0037037, -0.0023082], [0.0021292, -0.0025368], [0.001671, 0.0021344], [-0.0019914, 0.0010979], [-0.00071768, -0.0017109], [0.001379, -0.00029246], [-3.4953e-05, 0.001219], [-0.0010762, -0.00014045], [0.00016885, -0.00080944], [0.00054966, 0.0003023], [-0.00041285, 0.00046482], [-0.00041679, -0.00035115], [0.00025769, -0.0002443], [7.7295e-05, 0.00029995], [-0.00034897, 7.524e-05], [-0.00010391, -0.00024837], [0.0001322, -1.0763e-06], [-0.00010578, 0.00016165], [-0.00020879, -6.0143e-05], [-8.3546e-06, -0.00011623]])
    # Or load an input file
    #input = finesse.FinesseInput.read_input_file(os.path.join(local_home_path, rel_finesse_case_path, "INPUT", "finesse.inp"))
    #boundary = finesse.FinesseInput.read_boundary_file(os.path.join(local_home_path, rel_finesse_case_path, "DATA", "boundary.dat"))
    # Or load an input file with dialog
    #finesse_input = finesse.FinesseInput.load_input_dialog()

    # Load a target MATLAB file
    target = asdex.AsdexDataSet.load_matlab(os.path.join("example_files", "test_eq_AUG30382at2p5.mat"))

    finesse_input = finesse.FinesseInput(input, boundary, target.a_0, target.B_phi0)

    # Start the PF2q visual tool
    pf2qvis.FTool(session, finesse_input, target, input_path = local_input_path)

    plt.show()

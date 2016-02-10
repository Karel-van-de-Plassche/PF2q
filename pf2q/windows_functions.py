#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains the prototype functions that can be used to give
PF2q access to the system running FINESSE.
@licence: GPLv3
"""

import subprocess
import os


def make_send_input_boundary_pscp(finessePaths, pscp_path, putty_session,
                                  remote_user, remote_server):
    """
    Makes the function that temporarely saves the input and boundary data in
    the run directory and sends them to a remote server. It uses the PuTTY tool
    PSCP and assumes a PuTTY session exists and login is passwordless (for
    example, using ssh keys)
    """
    def send_input_boundary_pscp(input_data):

        run_dirname, __ = os.path.split(os.path.abspath(__file__))
        temp_input = os.path.join(run_dirname, "finesse.inp")
        temp_boundary = os.path.join(run_dirname, "boundary.dat")
        input_data.input_to_file(temp_input)
        input_data.boundary_to_file(temp_boundary)
        remote_input = finessePaths.path_module.join(finessePaths.INPUT_path,
                                                     "finesse.inp")
        remote_boundary = finessePaths.path_module.join(finessePaths.DATA_path,
                                                        "boundary.dat")
        remote_string = remote_user + "@" + remote_server
        subprocess.check_call(pscp_path + " -load " + putty_session + " " +
                              temp_input + " " + remote_string + ":" +
                              remote_input)
        subprocess.check_call(pscp_path + " -load " + putty_session + " " +
                              temp_boundary + " " + remote_string + ":" +
                              remote_boundary)
        os.remove(temp_input)
        os.remove(temp_boundary)
    return send_input_boundary_pscp


def make_run_finesse_gate(finessePaths, putty_path, putty_session,
                          remote_user, remote_gate, remote_server):
    """
    Makes the function that runs FINESSE on a remote server that needs to be
    reached through a gate server. It uses PuTTY and assumes a session exists
    and login is passwordless (for example, using ssh keys)
    FINESSE needs to be installed on the remote_server.
    """
    run_dirname, __ = os.path.split(os.path.abspath(__file__))
    command_file = os.path.join(run_dirname, "send_commands.txt")
    with open(command_file, 'w') as f:
        lines = ["ssh " + remote_server + " \"",
                 "ulimit -s unlimited && ",
                 "export PATH=$PATH:~/usr/local/bin && ",
                 "cd " + finessePaths.finesse_case_path + " && ",
                 "finesse\""]
        f.writelines(lines)

    def run_finesse_gate():
        command = putty_path + " -load " + putty_session + " -m "
        command += run_dirname + "\\send_commands.txt"
        subprocess.check_call(command)
    return run_finesse_gate


def make_copy_remote_ouput(finessePaths, pscp_path, putty_session,
                           remote_user, remote_gate):
    """
    Makes the function that copies FINESSE output data from a remote server
    to the local client. It assumes that the files reside on the remote_gate
    server, for example, when the server that FINESSE was run on an the
    remote_gate share a file system (like at DIFFER). It uses the PuTTY tool
    PSCP and assumes a PuTTY session exists and login is passwordless (for
    example, using ssh keys)
    """
    def copy_remote_ouput(result_path):
        remote_string = remote_user + "@" + remote_gate
        command = pscp_path + " -load " + putty_session + " " + remote_string
        command += ":" + finessePaths.OUTPUT_path + "*.dat " + result_path
        subprocess.check_call(command)
    return copy_remote_ouput


def make_remove_remote(finessePaths, putty_path, putty_session,
                       remote_user, remote_gate):
    """
    Makes the function that removes FINESSE output data and logs from a remote
    server. It assumes that the files reside on the remote_gate server, for
    example, when the server that FINESSE was run on an the remote_gate share
    a file system (like at DIFFER). It uses PuTTY and assumes a session exists
    and login is passwordless (for example, using ssh keys)
    """
    run_dirname, __ = os.path.split(os.path.abspath(__file__))
    command_file = os.path.join(run_dirname, "remove_commands.txt")
    with open(command_file, 'w') as f:
        lines = ["rm " + finessePaths.OUTPUT_path + "*.dat",
                 "rm " + finessePaths.OUTPUT_path + "*.log",
                 "rm " + finessePaths.OUTPUT_path + "*.inp"]
        lines = [line + "\n" for line in lines]
        f.writelines(lines)

    def remove_remote():
        command = putty_path + " -load " + putty_session + " -m "
        command += run_dirname + "\\remove_commands.txt"
        subprocess.check_call(command)
    return remove_remote


def make_save_input_boundary(local_INPUT_path, local_DATA_path):
    """
    Makes the function that saves the input and boundary data in the local
    input path. The function assumes that the local input path is
    accessible by the server running FINESSE, for example by a shared
    disk with the local client. This is the case at DIFFER.
    """
    def save_input_boundary(input_data):
        run_dirname, __ = os.path.split(os.path.abspath(__file__))
        input = os.path.join(local_INPUT_path, "finesse.inp")
        boundary = os.path.join(local_DATA_path, "boundary.dat")
        input_data.input_to_file(input)
        input_data.boundary_to_file(boundary)
    return save_input_boundary


def make_run_finesse(finessePaths, putty_path, putty_session,
                     remote_user, remote_server):
    """
    Makes the function that runs FINESSE on a remote server. It uses PuTTY
    and assumes a session exists and login is passwordless (for example,
    using ssh keys) FINESSE needs to be installed on the remote_server.
    """
    run_dirname, __ = os.path.split(os.path.abspath(__file__))
    command_file = os.path.join(run_dirname, "send_commands.txt")
    with open(command_file, 'w') as f:
        lines = ["ulimit -s unlimited && ",
                 "export PATH=$PATH:~/usr/local/bin && ",
                 "cd " + finessePaths.finesse_case_path + " && ",
                 "finesse"]
        f.writelines(lines)

    def run_finesse():
        command = putty_path + " -load " + putty_session + " -m "
        command += run_dirname + "\\send_commands.txt"
        subprocess.check_call(command)
    return run_finesse

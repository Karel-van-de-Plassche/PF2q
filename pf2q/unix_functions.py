#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains the prototype functions that can be used to give
PF2q access to the system running FINESSE.
@licence: GPLv3
"""

import subprocess
import os


def make_send_input_boundary(finessePaths, remote_user, remote_server):
    """
    Makes the function that temporarely saves the input and boundary data in
    the run directory and sends them to a remote server. It uses the Unix
    shell command scp and assumes login is passwordless (for example,
    using ssh keys)
    """
    def send_input_boundary(input_data):
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
        subprocess.check_call(["scp",
                               temp_input,
                               remote_string + ":" + remote_input])
        subprocess.check_call(["scp",
                               temp_boundary,
                               remote_string + ":" + remote_boundary])
        os.remove(temp_input)
        os.remove(temp_boundary)
    return send_input_boundary


def make_run_finesse_gate(finessePaths, remote_user,
                          remote_gate, remote_server):
    """
    Makes the function that runs FINESSE on a remote server that needs to be
    reached through a gate server. It uses the Unix shell command ssh and
    assumes login is passwordless (for example, using ssh keys)
    FINESSE needs to be installed on the remote_server.
    """
    def run_finesse_gate():
        remote_string = remote_user + "@" + remote_gate
        commands = ["ssh", remote_string,
                    "ssh " + remote_server + " \"ulimit -s unlimited &&  \
                    export PATH=$PATH:~/usr/local/bin && \
                    cd " + finessePaths.finesse_case_path + "  \
                    && finesse\""]
        subprocess.check_call(commands)
    return run_finesse_gate


def make_run_finesse_local(finessePaths):
    """
    Makes the function that runs FINESSE on a remote server that needs to be
    reached through a gate server. It uses the Unix shell command ssh and
    assumes login is passwordless (for example, using ssh keys)
    FINESSE needs to be installed on the remote_server.
    """
    def run_finesse_local(input, result):
        command = ["export PATH=$PATH:$HOME/usr/local/bin && cd " + \
                   finessePaths.finesse_case_path + " && finesse"]
        subprocess.check_call(command, shell=True)
    return run_finesse_local


def make_copy_remote_ouput(finessePaths, remote_user, remote_gate):
    """
    Makes the function that copies FINESSE output data from a remote server
    to the local client. It assumes that the files reside on the remote_gate
    server, for example, when the server that FINESSE was run on an the
    remote_gate share a file system (like at DIFFER). It uses the Unix shell
    command scp and assumes login is passwordless (for example, using ssh keys)
    """
    def copy_remote_ouput(result_path):
        remote_string = remote_user + "@" + remote_gate
        subprocess.check_call(["scp", "-r",
                               remote_string + ":" +
                               finessePaths.OUTPUT_path + "*.dat",
                               result_path])
    return copy_remote_ouput


def make_remove_remote(finessePaths, remote_user, remote_gate):
    """
    Makes the function that removes FINESSE output data and logs from a remote
    server. It assumes that the files reside on the remote_gate server, for
    example, when the server that FINESSE was run on an the remote_gate share
    a file system (like at DIFFER). It uses the Unix shell command ssh and
    assumes login is passwordless (for example, using ssh keys)
    """
    def remove_remote():
        remote_string = remote_user + "@" + remote_gate
        subprocess.check_call(["ssh",
                               remote_string,
                               ("rm " + finessePaths.OUTPUT_path + "*.dat " +
                                finessePaths.OUTPUT_path + "*.log " +
                                finessePaths.OUTPUT_path + "*.inp")])
    return remove_remote

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
This module provides a contolled execution of the real-time verifier. The control is given to a remote connection.
The remote connection can start a server, that will start the verifier process. The process can stop on its own when
all frames are collected or can be stopped by a remote connection.

"""

from multiprocessing import Process
from multiprocessing.managers import SyncManager
import multiprocessing as mp
import dquality.realtime.real_time as real
import argparse
import json
import sys
import time

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['parse_seq',
           'start_server',
           '__main__']


class Controller:
    """
    This class controlls execution of a real-time verifier. It contains a server that start the verifier process, and
    listens for connections. It accepts connection with the correct authentication key. The connection can execute
    only stop_process method that stops the process.

    """

    def __init__(self, config, report_file, sequence):
        self.config = config
        self.report_file = report_file
        self.sequence = sequence

    def CreateServer(self, port, key):
        """
        This function create an instance of SyncManager. It starts a verifier process.
        It registers stop_process method that will stop the process and is accessible by an authenticated remote
        connection.

        Parameters
        ----------
        port : int
            port the server listen on

        key : str
            a key to authenticate connection

        Returns
        -------
        manager : MyManager instance
            the created manager

        p : process
            a verifier process

        """

        def stop_verifier_process():
            #self.p.terminate()
            self.rt.finish()

        class MyManager(SyncManager):
            pass

        self.rt = real.RT()

        self.p = Process(target=self.rt.verify, args=(self.config, self.report_file, self.sequence, ))
        self.p.start()

        MyManager.register('stop_verifier_process', callable = stop_verifier_process)
        manager = MyManager(address = ('', port), authkey = key)
        return manager, self.p


def parse_seq(sequence):
    """
    This function evaluates the sequence parameter. If sequence is None or is empty, it will return None.
    Otherwise it returns json decoded list.

    Parameters
    ----------
    sequence : str
        a json string that contains a sequence of data types in experiment

    Returns
    -------
    json_sequence : list
        a list decoded from the json string or None if sequence was empty

    """

    try:
        seq = json.loads(sequence)
    except:
        seq = sequence
        if seq == 'None':
            seq = None
    return seq


def start_server(arg):
    """
    This function starts a real-time verifier application on a remote machine. It first starts a server that controls
    starting and stopping of the verifier. On starting the server this method will pass verifier arguments:
    configuration file, report file, and sequence, and server arguments: port, and key.
    After all started the functions checks periodically if the process is active. At the moment the process is
    inactive, the processing stops.

    Parameters
    ----------
    arg : list
        list of arguments that includes:
        config : str
            verifier configuration file
        report_file : str
            a file that the report will be saved
        sequence : list (converted from json string)
            a sequence of data types in experiment
        port : int
            a port on which the server listens
        key : str
            an authentication key for the remote communication

    Returns
    -------
    none

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("report_file")
    parser.add_argument("sequence")
    parser.add_argument("port")
    parser.add_argument("key")
    args = parser.parse_args()
    config = args.config
    report_file = args.report_file
    sequence = parse_seq(args.sequence)
    key = args.key


    controller = Controller(config, report_file, sequence)
    manager, p = controller.CreateServer(int(args.port), key)
    # this will start server
    manager.start()

    while True:
        time.sleep(2)
        if not p.is_alive():
            break
    time.sleep(1)


if __name__ == "__main__":
    start_server(sys.argv[1:])


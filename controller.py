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


"""

from multiprocessing.managers import SyncManager
import subprocess
import json
import uuid

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['start_verifier',
           'stop_verifier']


# Host and Port should be configured
# HOST = "txmtwo"
# PORT = "5011"
# VER_DIR = "/home/beams/USR32IDC/temp/"
HOST = ""
PORT = 5011
VER_DIR = "/local/bfrosik/data-quality"

def start_verifier(conf, report_file, variableDict):
    """
    This function starts a real-time verifier application on a remote machine. It first starts a server that controls
    starting and stopping of the verifier. On starting the server this method will pass verifier arguments:
    configuration file, report file, and sequence, and server arguments: port, and key.

    Parameters
    ----------
    conf : str
        configuration file on the remote machine where the verifier will execute

    report_file : str
        name of the report file that will be stored on the remote machine

    variableDict : dict
        a dictionary defining sequence of data type scanning

    Returns
    -------
    key : str
        a random string used for authentication

    """

    # variableDict = {'PreDarkImages': 5,
    #                 'PreWhiteImages': 10,
    #                 'Projections': 60,
    #                 'PostDarkImages': 5,
    #                 'PostWhiteImages': 10}
    sequence = []
    index = -1
    try:
        images = variableDict['PreDarkImages']
        index += images
        sequence.append(('data_dark', index))
    except KeyError:
        pass
    try:
        images = variableDict['PreWhiteImages']
        index += images
        sequence.append(('data_white', index))
    except KeyError:
        pass
    try:
        images = variableDict['Projections']
        index += images
        sequence.append(('data', index))
    except KeyError:
        pass
    try:
        images = variableDict['PostDarkImages']
        index += images
        sequence.append(('data_dark', index))
    except KeyError:
        pass
    try:
        images = variableDict['PostWhiteImages']
        index += images
        sequence.append(('data_white', index))
    except KeyError:
        pass

    json_sequence = json.dumps(sequence)
    key = uuid.uuid4()
    COMMAND="python " + VER_DIR + "server_verifier.py " + conf + ", " + report_file + ", " + json_sequence + \
            ", " + PORT + ", " + key

    ssh = subprocess.Popen(["ssh", "%s" % HOST, COMMAND],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    # key will be used to stop verifier
    return key

    #ssh usr32idc@txmtwo "python /home/beams/USR32IDC/temp/server_verifier.py conf, report_file, sequence, port, key"


def stop_verifier(key):
    """
    This method creates RemoteController instance that has a connection with remote server. Using this connection
    the code calls a 'stop_process' method on the remote server that will stop the verifier process.
    Then the connection is closed.

    Parameters
    ----------
    key : str
        a string generated in start_verifier method, user as authentication key

    Returns
    -------
    None
    """

    class RemoteController:
        def QueueServerClient(self, HOST, PORT, AUTHKEY):
            class QueueManager(SyncManager):
                pass
            QueueManager.register('stop_verifier_process')
            self.manager = QueueManager(address = (HOST, PORT), authkey = AUTHKEY)
            self.manager.connect()

        def stop_remote_process(self):
            self.manager.stop_verifier_process()
            try:
                conn = self.manager._Client(address = (HOST, PORT), authkey = key)
                conn.close()
            except Exception:
                pass

    remote_controller = RemoteController()

    # this will connect to the server
    remote_controller.QueueServerClient(HOST, PORT, key)

    # this will execute command on the server
    remote_controller.stop_remote_process()

stop_verifier('abc')


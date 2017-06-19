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
import sys
import argparse


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['stop_verifier']


HOST = ""

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

    parser = argparse.ArgumentParser()
    parser.add_argument("instrument", help="instrument name, name should have a matching directory in the .dquality folder")
    args = parser.parse_args()
    instrument = args.instrument
    
    if instrument == 'pilatus300':
        port = 5011
        key = 'pilatus300'
    elif instrument == 'S12-PILATUS1':
        port = 5012
        key = 'S12_PILATUS1'
    elif instrument == 'test':
        port = 5013
        key = 'test'
    else:
        print 'not supported instrument'

    class RemoteController:
        def QueueServerClient(self, HOST, port, key):
            class MyManager(SyncManager):
                pass
            MyManager.register('stop_verifier_process')
            self.manager = MyManager(address = (HOST, port), authkey = key)
            self.manager.connect()

        def stop_remote_process(self):
            self.manager.stop_verifier_process()
            try:
                conn = self.manager._Client(address = (HOST, port), authkey = key)
                conn.close()
            except Exception:
                pass

    remote_controller = RemoteController()

    # this will connect to the server
    remote_controller.QueueServerClient(HOST, port, key)

    # this will execute command on the server
    remote_controller.stop_remote_process()


if __name__ == "__main__":
    stop_verifier(sys.argv[1:])


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
Please make sure the installation :ref:`pre-requisite-reference-label` are met.

This module contains classes handling real time feedback of the quality results via process variables.

"""

from pcaspy import SimpleServer, Driver


class FbDriver(Driver):
    """
    This class is a driver that overrites write method and has a field counters.

    """
    def __init__(self, counters):
        """
        Constructor

        Parameters
        ----------
        counters : dict
            a dictionary where a key is pv (one for data type and quality method) and value is the number of
            failed frames

        """
        super(FbDriver, self).__init__()
        self.counters = counters

    def write(self, pv, index):
        """
        This function override write method fro Driver.

        It sets the 'index' pv to the index value, increments count of failing frames for the data type and quality
        check indicated by pv, and sets the 'counter' pv to the new counter value.

        Parameters
        ----------
        pv : str
            a name of the pv, contains information about the data type and quality check (i.e. data_white_mean)
        index : int
            index of failed frame

        Returns
        -------
        status : boolean
            Driver status

        """
        status = True
        self.setParam(pv+'_ind', index)
        self.counters[pv] += 1
        # this method is called on failed quality check, increase counter for this pv
        self.setParam(pv+'_ctr', self.counters[pv])
        self.updatePVs()
        return status

class FbServer:
    """
    This class is a server that controls the FbDriver.

    """
    def __init__(self):
        """
        Constructor

        """
        self.server = SimpleServer()

    def init_driver(self, detector, feedback_pvs):
        """
        This function initiates the driver.

        It creates process variables for the requested lidt of pv names. For each data type combination with the
        applicable quality check two pvs are created: one holding frame index, and one holding count of failed frames.
        It creates FbDriver instance and returns it to the calling function.

        Parameters
        ----------
        detector : str
            a pv name of the detector
        feedback_pvs : list
            a list of feedback process variables names, for each data type combination with the
            applicable quality check

        Returns
        -------
        driver : FbDriver
            FbDriver instance

        """
        prefix = detector + ':'
        pvdb = {}
        counters = {}
        for pv in feedback_pvs:
            pvdb[pv+'_ind'] = { 'prec' : 0,}
            pvdb[pv+'_ctr'] = { 'prec' : 0,
                                'hihi' : 1, }
            counters[pv] = 0

        self.server = SimpleServer()
        self.server.createPV(prefix, pvdb)

        driver = FbDriver(counters)
        return driver

    def activate_pv(self):
        """
        Infinite loop processing the pvs defined in server; exits when parent process exits.

        """
        while True:
            self.server.process(.1)

#if __name__ == '__main__':
    # args = sys.argv[1:]
    # parser = argparse.ArgumentParser()
    # parser.add_argument("instrument", help="instrument name, name should have a matching directory in the .dquality folder")
    # parser.add_argument("quality_checks", help="a list of quality check methods")
    # args = parser.parse_args()
    # instrument = args.instrument
    # quality_checks = args.quality_checks

    # feedback_pvs = ['mean', 'st_dev', 'stat_mean']
    # server, driver = init_driver('BBF1', feedback_pvs)
    # activate_pv()

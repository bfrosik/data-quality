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
import time
import dquality.clients.fb_client.pv_feedback as pvfb
import sys
if sys.version[0] == '2':
    import thread as thread
else:
    import _thread as thread


class PV_FB_12(pvfb.PV_FB):
    def __init__(self, **kwargs):
        super(PV_FB_12, self).__init__(**kwargs)


    def start_driver(self):
        server = FbServer_12()
        driver = server.init_driver(self.detector, self.feedback_pvs)
        thread.start_new_thread(server.activate_pv, ())
        self.driver = driver


    def write_to_pv(self, results):
        text = results.file_name
        if results.failed:
            msg = text + ' failed'
            for result in results.results:
                if result.error != 0:
                    qc = result.quality_id
                    msg =  msg + ' ' + qc + ' with result ' + str(result.res)
        else:
            msg = text + ' verification pass'
        self.driver.write(msg)


class FbDriver_12(pvfb.FbDriver):
    """
    This class is a driver that overrites write method.

    """
    def __init__(self, **kwargs):
        """
        Constructor

        Parameters
        ----------
        counters : dict
            a dictionary where a key is pv (one for data type and quality method) and value is the number of
            failed frames

        """
        super(FbDriver_12, self).__init__()


    def write(self, msg):
        """
        This function override write method from Driver.

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
        self.setParam('STAT', msg)
        self.updatePVs()
        return status


class FbServer_12(pvfb.FbServer):
    """
    This class is a server that controls the FbDriver.

    """

    def __init__(self):
        super(FbServer_12, self).__init__()


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

        pvdb['STAT'] = {
                            'type': 'char',
                            'count' : 300,
                            'value' : 'status'
                        }

        self.server.createPV(prefix, pvdb)

        driver = FbDriver_12()
        return driver

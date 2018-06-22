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

This module feeds the data coming from detector to a process using queue.
"""

import dquality.common.qualitychecks as ver
import dquality.clients.fb_client.simple_feedback as fb
import dquality.clients.zmq_client as zmq_client
import dquality.common.containers as containers
import dquality.common.constants as const
import pvaccess


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['start_feed',
           'stop_feed'
           'on_change']


class Feed:
    """
    This class reads frames in a real time, and delivers to consumers.
    """

    def __init__(self, logger, limits, quality_checks, feedback, zmq_snd_port, pva_name, detector):
        """
        Constructor
        """
        # for communication with pvaccess - receiving data
        self.data_type = 'data'
        self.pva_name = pva_name
        self.logger = logger
        self.limits = limits
        self.qc = quality_checks
        self.feedback = feedback
        self.zmq_snd_port = zmq_snd_port
        self.detector = detector
        if not self.feedback is None:
            self.feedback_obj = fb.Feedback(self.feedback, self.detector, self.quality_checks, self.logger)
        if not self.zmq_snd_port is None:
            self.cons = zmq_client.zmq_sen(self.zmq_snd_port)
        self.aggregate = containers.Aggregate(self.data_type, self.quality_checks)

        self.chan = None

    def feed_data(self):
        self.chan = pvaccess.Channel(self.pva_name)

        x, y = self.chan.get('field()')['dimension']
        self.dims = (y['size'], x['size'])
        print(self.dims)
        #send the dimensions to client
        data = containers.Data(const.DATA_STATUS_DIM)
        data.dim_x = x
        data.dim_y = y
        self.cons.send_to_zmq(data)

        labels = [item['name'] for item in self.chan.get('field()')['attribute']]
        self.theta_key = labels.index("SampleRotary")
        self.scan_delta_key = labels.index("ScanDelta")
        self.start_position_key = labels.index("StartPos")

        self.chan.subscribe('update', self.on_change)
        self.chan.startMonitor("value,attribute,uniqueId")


    def on_change(self, v):
        uniqueId = v['uniqueId']
        print('uniqueId: ', uniqueId)

        img = v['value'][0]['ushortValue']
        scan_delta = v["attribute"][self.scan_delta_key]["value"][0]["value"]
        start_position = v["attribute"][self.start_position_key]["value"][0]["value"]
        theta = (start_position + uniqueId * scan_delta) % 360.0

        img = img.reshape(self.dims)

        data = containers.Data(const.DATA_STATUS_DATA, img, self.data_type)
        frame_results = ver.run_quality_checks(data, uniqueId, self.aggregate, self.limits, self.quality_checks)

        if not self.feedback is None:
            self.feedback_obj.deliver(frame_results)

        if not self.zmq_snd_port is None:
            data.theta = theta
            data.image_number = uniqueId
            data.ver = not frame_results.failed
            self.cons.send_to_zmq(data)


    def stop_feed(self):
        # stop getting data
        self.chan.stopMonitor()
        self.chan.unsubscribe('update')

        # nothing to do to terminate updating of feedback pvs (maybe zero them?)

        # terminate zmq connection
        data = containers.Data(const.DATA_STATUS_END)
        self.cons.send_to_zmq(data)


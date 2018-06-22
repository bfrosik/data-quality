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

This module feeds the data coming from detector to a process using queue. It interracts with a channel access
plug in of area detector. The read of frame data from channel access happens on event of frame counter change.
The change is detected with a callback. The data is passed to the consuming process.
This module requires configuration file with the following parameters:
'detector', a string defining the first prefix in area detector.
'no_frames', number of frames that will be fed
'args', optional, list of process specific parameters, they need to be parsed to the desired format in the wrapper
"""

from multiprocessing import Process, Queue
import json
import sys
import time
import dquality.common.utilities as utils
import dquality.common.report as report
from dquality.feeds.pv_feed import Feed
import dquality.common.constants as const
import dquality.clients.fb_client.feedback as fb
import dquality.feeds.adapter as adapter
from dquality.feeds.pv_feed_decorator import FeedDecorator


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'RT.verify',
           'RT.finish']


def init(config):
    """
    This function initializes variables according to configuration.

    It gets values from the configuration file, evaluates and processes the values. If mandatory parameter is missing,
    the script logs an error and exits.

    Parameters
    ----------
    config : str
        configuration file name, including path

    Returns
    -------
    logger : Logger
        logger instance

    limits : dictionary
        a dictionary containing limit values read from the configured 'limit' file

    quality_checks : dict
        a dictionary containing quality check functions ids

    feedback : list
        a list of strings defining real time feedback of quality checks errors. Currently supporting 'PV', 'log', and
        'console'

    report_type : int
        report type; currently supporting 'none', 'error', and 'full'

    consumers : dict
        a dictionary parsed from json file representing consumers

    """
    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    feed_args = []
    feed_kwargs = {}

    limitsfile = utils.get_file(conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())
    feed_args.append(limits)

    qcfile = utils.get_file(conf, 'quality_checks', logger)
    if qcfile is None:
        sys.exit(-1)

    with open(qcfile) as qc_file:
        dict = json.loads(qc_file.read())
    feed_args.append(dict)

    try:
        no_frames = int(conf['no_frames'])
    except KeyError:
        print ('no_frames parameter not configured. Continuous mode.')
        no_frames = -1
    feed_args.append(no_frames)

    try:
        callback_pv = conf['callback_pv']
        feed_kwargs['callback_pv'] = callback_pv
    except KeyError:
        pass

    try:
        detector = conf['detector']
        feed_kwargs['detector'] = detector
    except KeyError:
        print ('detector parameter not configured.')
        sys.exit(-1)

    try:
        consumers = conf['zmq_snd_port']
        feed_kwargs['consumers'] = consumers
    except KeyError:
        pass

    try:
        aggregate_limit = int(conf['aggregate_limit'])
    except KeyError:
        aggregate_limit = no_frames
    feed_kwargs['aggregate_limit'] = aggregate_limit

    try:
        feedback = conf['feedback_type']
        if len(feedback) == 0:
            feedback = None
    except KeyError:
        feedback = None

    try:
        decor_conf = conf['decor']
        decor_map = {}
        for entry in decor_conf:
            entry = entry.split('>')
            decor_map[entry[0].strip()] = entry[1].strip()
        if len(decor_map) == 0:
            decor_map = None
    except KeyError:
        decor_map = None

    try:
        report_type = conf['report_type']
    except KeyError:
        report_type = const.REPORT_FULL

    return feed_args, feed_kwargs, feedback, decor_map, logger, report_type


class RT:

    def verify(self, config, report_file=None, sequence = None):
        """
        This function starts real time verification process according to the given configuration.

        This function reads configuration and initiates variables accordingly.
        It creates a Feed instance and starts data_feed and waits to receive results in aggregateq.
        The results are then written into a report file.

        Parameters
        ----------
        conf : str
            configuration file name, including path

        report_file : file
            a file where the report will be written, defaulted to None, if no report wanted

        sequence : list or int
            information about data sequence or number of frames

        Returns
        -------
        boolean

        """
        feed_args, feed_kwargs, feedback, decor_map, logger, report_type = init(config)

        # init the pv feedback
        if not feedback is None:
            feedbackq = Queue()
            feedback_pvs = utils.get_feedback_pvs(feed_args[1])
            fb_args = {'feedback_pvs':feedback_pvs, 'detector':feed_kwargs['detector']}
            feedback_obj = fb.Feedback(feedbackq, feedback, **fb_args)
            # put the logger to args
            if const.FEEDBACK_LOG in feedback:
                feedback_obj.set_logger(logger)
            feed_kwargs['feedbackq'] = feedbackq

            self.p = Process(target=feedback_obj.deliver, args=())
            self.p.start()

        reportq = Queue()

        # address the special cases of quality checks when additional arguments are required
        if decor_map is None:
            self.feed = Feed()
        else:
            self.feed = FeedDecorator(decor_map)

        ack = self.feed.feed_data(logger, reportq, *feed_args, **feed_kwargs)
        if ack == 1:
            bad_indexes = {}

            aggregate = reportq.get()

            if report_file is not None:
                report.report_results(logger, aggregate, None, report_file, report_type)
            report.add_bad_indexes(aggregate, bad_indexes)

            return bad_indexes


    def finish(self):
        try:
            self.feed.finish()
            time.sleep(1)
        except:
            pass

        try:
            self.p.terminate()
        except:
            pass


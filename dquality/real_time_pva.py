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

import json
import signal
import sys
import dquality.common.utilities as utils
from dquality.feeds.pva_feed import Feed


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

    zmq_snd_port : int
        a port used to send the verified data out

    pva_name : str
        pvaccess name

    detector : str
        detector name

    """
    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    try:
        pva_name = conf['pva_name']
    except KeyError:
        print ('pva_name not configured')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    limitsfile = utils.get_file(conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())

    qcfile = utils.get_file(conf, 'quality_checks', logger)
    if qcfile is None:
        sys.exit(-1)

    with open(qcfile) as qc_file:
        dict = json.loads(qc_file.read())
    quality_checks = dict

    try:
        feedback = conf['feedback_type']
        if len(feedback) == 0:
            feedback = None
    except KeyError:
        feedback = None

    try:
        zmq_snd_port = conf['zmq_snd_port']
    except KeyError:
        zmq_snd_port = None

    try:
        detector = conf['detector']
    except KeyError:
        print ('detector parameter not configured.')
        detector = None

    return logger, limits, quality_checks, feedback, zmq_snd_port, pva_name, detector


class RT:

    def verify(self, config):
        """
        This function starts real time verification process according to the given configuration.

        Parameters
        ----------
        conf : str
            configuration file name, including path

        Returns
        -------
        none

        """
        logger, limits, quality_checks, feedback, zmq_snd_port, pva_name, detector = init(config)

        self.feed = Feed(logger, limits, quality_checks, feedback, zmq_snd_port, pva_name, detector)
        self.feed.feed_data()


    def finish(self):
        """
        This function gracefully terminates the pvaccess feed and it's clients

        """
        print ('finish')
        self.feed.stop_feed()


def signal_handler(signal, frame):
    rt.finish()

rt = RT()
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

rt.verify('/home/phoebus/BFROSIK/.dquality/BBF1/dqconfig.ini')

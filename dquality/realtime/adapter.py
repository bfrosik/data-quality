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

This module is an adapter connecting feed with a consuming process.
The functions in this module are customized for the consuming process. All functions must be implemented, as they
are called by the feed module.

"""

from multiprocessing import Process
from dquality.handler import handle_data
import dquality.common.containers as containers
import dquality.common.constants as const
import dquality.common.utilities as utils


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['start_process',
           'parse_config',
           'pack_data']



def start_process(dataq, logger, *args):
    """
    This function parses parameters and starts process consuming frames from feed.

    This function parses the positional parameters. Then it starts a client process, passing in a queue as first
    parameter, followed by the parsed parameters. The function of the client process must be included in imports.

    Parameters
    ----------
    dataq : multiprocessing.Queue
        a queue used to transfer data from feed to client process

    logger : Logger
        an instance of Logger, used by the application

    *args : list
        a list of posisional parameters required by the client process

    Returns
    -------
    none
    """
    limits = args[0]
    reportq = args[1]
    quality_checks = args[2]
    aggregate_limit = args[3]
    consumers = args[4]
    feedback = args[5]

    feedback_obj = containers.Feedback(feedback)
    if const.FEEDBACK_LOG in feedback:
        feedback_obj.set_logger(logger)

    if const.FEEDBACK_PV in feedback:
        feedback_pvs = utils.get_feedback_pvs(quality_checks)
        detector = args[6]
        feedback_obj.set_feedback_pv(feedback_pvs, detector)

    p = Process(target=handle_data, args=(dataq, limits, reportq, quality_checks, aggregate_limit, consumers, feedback_obj))
    p.start()


def parse_config(config):
    """
    This function parses the configuration file.

    It must return the specified variables.

    Parameters
    ----------
    config : str
        a configuration file

    Returns
    -------
    no_frames : int
        number of frames that will be processed

    detector : str
        a string defining the first prefix in area detector, it has to match the area detector configuration

    detector_basic : str
        a string defining the second prefix in area detector, defining the basic parameters, it has to
        match the area detector configuration

    detector_image : str
        a string defining the second prefix in area detector, defining the image parameters, it has to
        match the area detector configuration

    """

    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    try:
        no_frames = conf['no_frames']
    except KeyError:
        print ('no_frames parameter not configured.')
        return None
    try:
        aggregate_limit = conf['aggregate_limit']
    except KeyError:
        #print ('aggregate_limit parameter not configured.')
        aggregate_limit = no_frames
    try:
        detector = conf['detector']
    except KeyError:
        print ('configuration error: detector parameter not configured.')
        return None
    try:
        detector_basic = conf['detector_basic']
    except KeyError:
        print ('configuration error: detector_basic parameter not configured.')
        return None
    try:
        detector_image = conf['detector_image']
    except KeyError:
        print ('configuration error: detector_image parameter not configured.')
        return None

    return int(no_frames), aggregate_limit, detector, detector_basic, detector_image


def pack_data(slice, type):
    """
    This function packs a single image data into a specific container.

    Parameters
    ----------
    slice : nparray
        image data

    type : str
       data type, as 'data', 'data_white', or 'data_dark'

    """
    if slice is not None:
        return containers.Data(const.DATA_STATUS_DATA, slice, type)
    elif type == 'missing':
        return containers.Data(const.DATA_STATUS_MISSING)
    else:
        return containers.Data(const.DATA_STATUS_END)

def pack_data_with_decor(slice, type, acq_time):
    """
    This function packs a single image data into a specific container.

    Parameters
    ----------
    slice : nparray
        image data

    type : str
       data type, as 'data', 'data_white', or 'data_dark'

    """
    if slice is not None:
        return containers.Data(const.DATA_STATUS_DATA, slice, type, acq_time)
    elif type == 'missing':
        return containers.Data(const.DATA_STATUS_MISSING)
    else:
        return containers.Data(const.DATA_STATUS_END)


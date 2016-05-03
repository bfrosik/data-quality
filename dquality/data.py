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

This module verifies a configured hd5 file. The data is verified against configured
"limits" file. The limits are applied by processes performing specific quality calculations.

The results is a detail report of calculated values. The indexes of slices that did not pass
quality check are returned back.

"""

import os
import json
import sys
from configobj import ConfigObj
from os.path import expanduser
from multiprocessing import Queue, Process
import dquality.common.utilities as utils
import dquality.handler as handler
from dquality.common.containers import Data
import dquality.common.report as report

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['process_data']

home = expanduser("~")
config = os.path.join(home, 'dqconfig.ini')
conf = ConfigObj(config)
logger = utils.get_logger(__name__, conf)


file = utils.get_file(home, conf, 'file', logger)
if file is None:
    sys.exit(-1)


limitsfile = utils.get_file(home, conf, 'limits', logger)
if limitsfile is None:
    sys.exit(-1)

with open(limitsfile) as limits_file:
    limits = json.loads(limits_file.read())['limits']

fp, tags = utils.get_data_hd5(file)

def process_data(dataq, data_type, aggregateq):
    """
    This method creates and starts a new handler process. The handler is initialized with data queue,
    the data type, and a result queue. The data type can be 'data_dark', 'data_white' or 'data'.
    After starting the process the function enqueues queue slice by slice into data, until all data is
    queued. The last enqueued element is end of the data marker.

    Parameters
    ----------
    dataq : Queue
        data queue; used to pass 2D arrays (slices) to the handler

    data_type : str
        string indicating what type of data is processed.

    aggregateq : Queue
        result queue; used by handler to enqueue results

    Returns
    -------
    None
    """
    try:
        data_tag = tags['/exchange/'+data_type]
        data = fp[data_tag]
    except KeyError:
        logger.warning('the hd5 file does not contain data of the type ' + data_type)
        dataq.put('all_data')
        return

    p = Process(target=handler.handle_data, args=(dataq, limits[data_type], aggregateq, ))
    p.start()

    for i in range(0,data.shape[0]):
        dataq.put(Data(data[i]))
    dataq.put('all_data')

def verify():
    """
    This invokes sequentially data verification processes for data_dark, data_white, and data that is contained
    in configured hd5 file. The calculated values are check against limits, configured in a file.
    Each process gets two queues parameters; one queue to get the data, and second queue to
    pass back the results.
    The function awaits results from the response queues in the matching sequence to how the
    processes started.
    The results are retrieved as json object.
    The indexes of slices that did not pass quality check are reported to the calling function in form of dictionary.

    Parameters
    ----------
    None

    Returns
    -------
    Dict
    A dictionary containing indexes of slices that did not pass quality check. The key is a type of data.
    (i.e. data_dark, data_white,data)
    """
    #process data_dark
    data_dark_q = Queue()
    process_data(Queue(),'data_dark',data_dark_q)

    #process data_white
    data_white_q = Queue()
    process_data(Queue(),'data_white', data_white_q)

    #process data
    data_q = Queue()
    process_data(Queue(),'data', data_q)

    # find from config how to report the results
    report_file = None
    try:
        report_file_name = conf['report_file']
        try:
            report_file = open(report_file_name, 'w')
        except:
            logger.warning('Cannot open report file, writing report on console')
    except KeyError:
        logger.info('report file not configured, writing report on console')

    bad_indexes = {}

    # receive the results
    aggregate_data_dark = data_dark_q.get()
    report.report_results(aggregate_data_dark, 'data_dark', report_file)
    report.add_bad_indexes(aggregate_data_dark, 'data_dark', bad_indexes)

    aggregate_data_white = data_white_q.get()
    report.report_results(aggregate_data_white, 'data_white', report_file)
    report.add_bad_indexes(aggregate_data_white, 'data_white', bad_indexes)

    aggregate_data = data_q.get()
    report.report_results(aggregate_data, 'data', report_file)
    report.add_bad_indexes(aggregate_data, 'data', bad_indexes)

    return bad_indexes

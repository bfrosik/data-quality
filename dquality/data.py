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
import os.path
import json
import sys
import string
from multiprocessing import Queue, Process
import dquality.common.utilities as utils
import dquality.handler as handler
from dquality.common.containers import Data
import dquality.common.report as report

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'process_data',
           'verify_file',
           'verify']


def init(config):
    """
    This function initializes global variables. It gets values from the configuration file, evaluates and processes
    the values. If mandatory file or directory is missing, the script logs an error and exits.

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

    report_file : str
        a report file configured in a given configuration file
    """

    conf = utils.get_config(config)

    logger = utils.get_logger(__name__, conf)

    limitsfile = utils.get_file(conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())['limits']

    return logger, limits

def process_data(data_type, aggregateq, fp, data_tag, limits):
    """
    This method creates and starts a new handler process. The handler is initialized with data queue,
    the data type, and a result queue. The data type can be 'data_dark', 'data_white' or 'data'.
    After starting the process the function enqueues queue slice by slice into data, until all data is
    queued. The last enqueued element is end of the data marker.

    Parameters
    ----------
    data_type : str
        string indicating what type of data is processed.

    aggregateq : Queue
        result queue; used by handler to enqueue results

    fp : file pointer
        a pointer to the file that is verifier

    data_tag : str
        a data tag to look for

    limits : dict
        a dictionary of limits values

    Returns
    -------
    None
    """
    dt = fp[data_tag]

    dataq = Queue()

    p = Process(target=handler.handle_data, args=(dataq, limits[data_type], aggregateq, ))
    p.start()

    for i in range(0,dt.shape[0]):
        dataq.put(Data(dt[i]))
    dataq.put('all_data')


def verify_file(logger, file, limits, report_file):
    """
    This method creates and starts a new handler process. The handler is initialized with data queue,
    the data type, and a result queue. The data type can be 'data_dark', 'data_white' or 'data'.
    After starting the process the function enqueues queue slice by slice into data, until all data is
    queued. The last enqueued element is end of the data marker.

    Parameters
    ----------
    logger: Logger
        Logger instance.

    file : str
        a filename including path that will be verified

    limits : dict
        a dictionary of limits values

    report_file : str
        a name of a report file

    Returns
    -------
    bad_indexes : dict
        a dictionary of bad indexes per data type

    """
    fp, tags = utils.get_data_hd5(file)

    if report_file is not None:
        try:
            report_file = open(report_file, 'w')
        except:
            logger.warning('Cannot open report file')
            report_file = None

    types = ['data_dark', 'data_white', 'data']
    queues = {}
    bad_indexes = {}

    for type in types:
        data_tag = '/exchange/'+ type
        if data_tag in tags:
            queues[type] = Queue()

    for type in queues.keys():
        queue = queues[type]
        data_tag = '/exchange/'+ type
        process_data(type, queue, fp, data_tag, limits)


    # receive the results
    for type in queues.keys():
        queue = queues[type]
        aggregate = queue.get()
        if report_file is not None:
            report.report_results(aggregate, type, file, report_file)
        report.add_bad_indexes(aggregate, type, bad_indexes)

    return bad_indexes


def verify(conf, file):
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
    conf : str
        name of the configuration file including path. If contains only directory, 'dqconfig_test.ini' will a default
        file name.

    file : str
        file name to do the quality checks on

    Returns
    -------
    bad_indexes : Dict
        A dictionary containing indexes of slices that did not pass quality check. The key is a type of data.
        (i.e. data_dark, data_white,data)
    """

    logger, limits = init(conf)
    if not os.path.isfile(file):
        logger.error(
            'parameter error: file ' +
            file + ' does not exist')
        sys.exit(-1)

    report_file = file.rsplit(".",)[0] + '.report'

    return verify_file(logger, file, limits, report_file)

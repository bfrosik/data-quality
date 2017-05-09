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
import numpy as np
from multiprocessing import Queue, Process
import dquality.common.utilities as utils
import dquality.handler as handler
from dquality.common.containers import Data
import dquality.common.report as report
import dquality.common.constants as const
import time

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'verify_file_hdf',
           'verify_file_ge',
           'verify']


def init(config):
    """
    This function initializes variables according to configuration.

    It gets values from the configuration file, evaluates and processes the values. If mandatory file or directory
    is missing, the script logs an error and exits.

    Parameters
    ----------
    config : str
        configuration file name, including path

    Returns
    -------
    logger : Logger
        logger instance

    data_tags : dict
        a dictionary od data_type/hdf tag

    limits : dictionary
        a dictionary containing limit values read from the configured 'limit' file

    quality_checks : dict
        a dictionary containing quality check functions ids

    file_type : int
        data file type; currently supporting FILE_TYPE_HDF and FILE_TYPE_GE

    report_type : int
        report type; currently supporting 'none', 'error', and 'full'

    report_dir : str
        a directory where report files will be located

    consumers : dict
        a dictionary containing consumer processes to run, and their parameters

    """

    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    try:
        file_type = conf['file_type']
    except KeyError:
        file_type = const.FILE_TYPE_HDF

    if file_type == const.FILE_TYPE_HDF:
        tagsfile = utils.get_file(conf, 'data_tags', logger)
        if tagsfile is None:
            sys.exit(-1)
        with open(tagsfile) as tags_file:
            data_tags = json.loads(tags_file.read())
    else:
        data_tags = None

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
    quality_checks = utils.get_quality_checks(dict)

    try:
        report_type = conf['report_type']
    except KeyError:
        report_type = const.REPORT_FULL

    try:
        report_dir = conf['report_dir']
        if not os.path.isdir(report_dir):
            report_dir = None
    except KeyError:
        report_dir = None

    consumersfile = utils.get_file(conf, 'consumers', logger, False)
    if consumersfile is None:
        consumers = None
    else:
        with open(consumersfile) as consumers_file:
            consumers = json.loads(consumers_file.read())

    return logger, data_tags, limits, quality_checks, file_type, report_type, report_dir, consumers


def verify_file_hdf(logger, file, data_tags, limits, quality_checks, report_type, report_dir, consumers):
    """
    This method handles verification of data in hdf type file.

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

    data_tags : dict
        a dictionary od data_type/hdf tag

    limits : dict
        a dictionary of limits values

    quality_checks : dict
        a dictinary specifying quality checks structure that will be applied to verify the data file

    report_type : int
        report type, currently supporting 'none', 'errors', and 'full'

    report_dir : str
        a directory where report files will be located

    consumers : dict
        a dictionary containing consumer processes to run, and their parameters

    Returns
    -------
    bad_indexes : dict
        a dictionary of bad indexes per data type

    """
    def process_data(data_type):
        data_tag = data_tags[data_type]
        dt = fp[data_tag]
        for i in range(0,dt.shape[0]):
            data = Data(const.DATA_STATUS_DATA, dt[i], data_type)
            dataq.put(data)
            # add delay to slow down flow up, so the flow down (results)
            # are handled in synch
            time.sleep(.1)

    fp, tags = utils.get_data_hdf(file)
    dataq = Queue()
    aggregateq = Queue()

    p = Process(target=handler.handle_data, args=(dataq, limits, aggregateq, quality_checks, consumers))
    p.start()

    # assume a fixed order of data types; this will determine indexes on the data
    if 'data_dark' in data_tags:
        process_data('data_dark')
    if 'data_white' in data_tags:
        process_data('data_white')
    if 'data' in data_tags:
        process_data('data')

    dataq.put(Data(const.DATA_STATUS_END))


    if report_type != const.REPORT_NONE:
        if report_dir is None:
            report_file = file.rsplit(".",)[0] + '.report'
        else:
            file = file.rsplit(".",)[0]
            file_path = file.rsplit("/",)
            report_file = report_dir + "/" + file_path[len(file_path-1)]+ '.report'

    # receive the results
    bad_indexes = {}
    aggregate = aggregateq.get()

    if report_file is not None:
        report.report_results(logger, aggregate, None, report_file, report_type)
    report.add_bad_indexes(aggregate, bad_indexes)

    logger.info('data verifier evaluated ' + file + ' file')
    return bad_indexes


def verify_file_ge(logger, file, limits, quality_checks, report_type, report_dir, consumers):
    """
    This method handles verification of data in a ge file type.
    This method creates and starts a new handler process. The handler is initialized with data queue,
    the data type, which is 'data', and a result queue.
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

    quality_checks : dict
        a dictinary specifying quality checks structure that will be applied to verify the data file

    report_type : int
        report type, currently supporting 'none', 'errors', and 'full'

    report_dir : str
        a directory where report files will be located

    consumers : dict
        a dictionary containing consumer processes to run, and their parameters

    Returns
    -------
    bad_indexes : dict
        a dictionary of bad indexes per data type

    """
    type = 'data'

    fp, nframes, fsize = utils.get_data_ge(logger, file)
    # data file is corrupted, error message is logged
    if fp is None:
        return None

    dataq = Queue()
    aggregateq = Queue()

    p = Process(target=handler.handle_data, args=(dataq, limits, aggregateq, quality_checks, consumers))
    p.start()

    for i in range(0,nframes):
        img = np.fromfile(fp,'uint16', fsize)
        dataq.put(Data(const.DATA_STATUS_DATA, img, type))
        time.sleep(.2)
    dataq.put(Data(const.DATA_STATUS_END))

    # receive the results
    bad_indexes = {}
    aggregate = aggregateq.get()
    report.add_bad_indexes(aggregate, bad_indexes)

    if report_type != const.REPORT_NONE:
        if report_dir is None:
            report_file = file + '.report'
        else:
            file_path = file.rsplit("/",)
            report_file = report_dir + "/" + file_path[len(file_path)-1]+ '.report'

        report.report_results(logger, aggregate, file, report_file, report_type)

    logger.info('data verifier evaluated ' + file + ' file')

    return bad_indexes


def verify(conf, file):
    """
    This function verifies data in a given file.

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

    logger, data_tags, limits, quality_checks, file_type, report_type, report_dir, consumers  = init(conf)
    if not os.path.isfile(file):
        logger.error(
            'parameter error: file ' +
            file + ' does not exist')
        sys.exit(-1)

    if file_type == const.FILE_TYPE_HDF:
        return verify_file_hdf(logger, file, data_tags, limits, quality_checks, report_type, report_dir, consumers)
    elif file_type == const.FILE_TYPE_GE:
        return verify_file_ge(logger, file, limits, quality_checks, report_type, report_dir, consumers)

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

The application monitors given directory for new/modified files of the
given pattern. Each of the detected file is verified according to schema
configuration and for each of the file several new processes are started,
each process performing specific quality calculations.

The results will be sent to an EPICS PV (printed on screen for now).

"""

import os
import sys
import pyinotify
from pyinotify import WatchManager
from multiprocessing import Process, Queue
import json
import numpy as np
import dquality.common.utilities as utils
import dquality.handler as datahandler
import dquality.common.report as report
import dquality.common.constants as const
from dquality.common.containers import Data

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'verify',
           'directory']

files = Queue()
INTERRUPT = 'interrupt'


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

    limits : dictionary
        a dictionary containing limit values read from the configured 'limit' file

    quality_checks : dict
        a dictionary containing quality check functions ids

    extensions : list
        a list containing extensions of files to be monitored read from the configuration file

    report_type : int
        report type; currently supporting 'none', 'error', and 'full'

    consumers : dict
        a dictionary containing consumer processes to run, and their parameters

    """
    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    limitsfile = utils.get_file(conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())

    try:
        extensions = conf['extensions']
    except KeyError:
        logger.warning('no file extension specified. Monitoring for all files.')
        extensions = ['']

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

    consumersfile = utils.get_file(conf, 'consumers', logger, False)
    if consumersfile is None:
        consumers = None
    else:
        with open(consumersfile) as consumers_file:
            consumers = json.loads(consumers_file.read())

    return logger, limits, quality_checks, extensions, report_type, consumers


def directory(directory, patterns):
    """
    This method monitors a directory given by the "*directory*" parameter.

    It creates a notifier object. The notifier is registered to await
    the "*CLOSE_WRITE*" event on a new file that matches the "*pattern*"
    parameter. If there is no such event, it yields control on timeout,
    defaulted to 1 second. It returns the created notifier.

    Parameters
    ----------
    directory : str
        File Name including path

    patterns : list
        A list of strings representing file extension

    Returns
    -------
    notifier : Notifier
        a Notifier instance
    """
    class EventHandler(pyinotify.ProcessEvent):

        def process_IN_CLOSE_WRITE(self, event):
            for pattern in patterns:
                file = event.pathname
                if file.endswith(pattern):
                        files.put(event.pathname)
                        break

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler, timeout=1)
    wdd = wm.add_watch(directory, mask, rec=False)
    return notifier

def verify(conf, folder, data_type, num_files, report_by_files=True):
    """
    This function discovers new files and evaluates data in the files.

    This is the main function called when the verifier application starts.
    It reads the configuration for the directory to monitor, for pattern
    that represents a file extension to look for, and for a number of
    files that are expected for the experiment. The number of files
    configuration parameter is added for experiments that generate
    multiple files. In some cases the experiment data is collected
    into a single file, which is organized with data sets.

    The function calls directory function that sets up the monitoring
    and returns notifier. After the monitoring is initialized, it starts
    a loop that reads the global "*files*" queue and then the global
    "*results*" queue. If there is any new file, the file is removed
    from the queue, and the data in the file is validated by a sequence
    of validation methods. If there is any new result, the result is
    removed from the queue, corresponding process is terminated, and
    the result is presented. (currently printed on console, later will
    be pushed into an EPICS process variable)

    The loop is interrupted when all expected processes produced results.
    The number of expected processes is determined by number of files and
    number of validation functions.

    Parameters
    ----------
    conf : str
        configuration file name, including path

    folder : str
        monitored directory

    data_type : str
        defines which data type is being evaluated

    num_files : int
        number of files that will be processed

    report_by_files : boolean
        this variable directs how to present the bad indexes in a report. If True, the indexes
        are related to the files, and a filename is included in the report. Otherwise, the
        report contains a list of bad indexes.

    Returns
    -------
    bad_indexes : dict
        a dictionary or list containing bad indexes

    """
    logger, limits, quality_checks, extensions, report_type, consumers = init(conf)
    if not os.path.isdir(folder):
        logger.error(
            'parameter error: directory ' +
            folder + ' does not exist')
        sys.exit(-1)

    notifier = directory(folder, extensions)

    interrupted = False
    file_list = []
    offset_list = []
    dataq = Queue()
    aggregateq = Queue()
    p = Process(target=datahandler.handle_data, args=(dataq, limits, aggregateq, quality_checks, consumers))
    p.start()

    file_index = 0
    slice_index = 0
    while not interrupted:
        # The notifier will put a new file into a newFiles queue if one was
        # detected
        notifier.process_events()
        if notifier.check_events():
            notifier.read_events()

        # checking the newFiles queue for new entries and starting verification
        # processes for each new file
        while not files.empty():
            file = files.get()
            if file.find('INTERRUPT') >= 0:
                # the calling function may use a 'interrupt' command to stop the monitoring
                # and processing.
                dataq.put(Data(const.DATA_STATUS_END))
                notifier.stop()
                interrupted = True
                break
            else:
                if file_index == 0:
                    report_file = file.rsplit(".",)[0] + '.report'
                fp, tags = utils.get_data_hdf(file)
                data_tag = tags['/exchange/'+data_type]
                data = np.asarray(fp[data_tag])
                slice_index += data.shape[0]
                file_list.append(file)
                offset_list.append(slice_index)
                for i in range(0, data.shape[0]):
                    dataq.put(Data(const.DATA_STATUS_DATA, data[i], data_type))
                file_index += 1
                if file_index == num_files:
                    dataq.put(Data(const.DATA_STATUS_END))
                    notifier.stop()
                    interrupted = True
                    break

    aggregate = aggregateq.get()

    #report.report_results(logger, aggregate, data_type, None, report_file, report_type)

    bad_indexes = {}
    if report_by_files == 'True':
        report.add_bad_indexes_per_file(aggregate, bad_indexes, file_list, offset_list)
    else:
        report.add_bad_indexes(aggregate, bad_indexes)
    try:
        report_file = open(report_file, 'w')
        report.report_bad_indexes(bad_indexes, report_file)
    except:
        logger.warning('Cannot open report file')


    return bad_indexes


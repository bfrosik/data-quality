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
from os.path import expanduser
from configobj import ConfigObj
from pyinotify import WatchManager
from multiprocessing import Process, Queue
import json
import numpy as np

import dquality.common.utilities as utils
import dquality.handler as datahandler
import dquality.common.report as report
from dquality.common.containers import Data

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['verify',
           'directory']

home = expanduser("~")
config = os.path.join(home, 'dqconfig.ini')
conf = ConfigObj(config)
logger = utils.get_logger(__name__, conf)

logger.info('monitoring')

files = Queue()
INTERRUPT = 'interrupt'

def directory(directory, patterns):
    """
    This method monitors a directory given by the "*directory*" parameter.
    It creates a notifier object. The notifier is registered to await
    the "*CLOSE_WRITE*" event on a new file that matches the "*pattern*"
    parameter. If there is no such event, it yields control on timeout,
    defaulted to 1 second. It returns the created notifier.

    Parameters
    ----------
    file : str
        File Name including path

    patterns : list
        A list of strings representing file extension

    Returns
    -------
    None
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

def verify(data_type, num_files, report_by_files):
    """
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
    None

    Returns
    -------
    None
    """
    logger.info('monitoring directory')
    interrupted = False
    folder = utils.get_directory(conf, logger)
    if folder is None:
        sys.exit(-1)

    limitsfile = utils.get_file(home, conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())['limits']

    try:
        notifier = directory(folder, conf['extensions'])
    except KeyError:
        logger.warning('no file extension specified. Monitoring for all files.')
        notifier = directory(folder, None)

    file_indexes = {}
    dataq = Queue()
    aggregateq = Queue()
    p = Process(target=datahandler.handle_data, args=(dataq, limits[data_type], aggregateq, ))
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
            if file == INTERRUPT:
                # the calling function may use a 'interrupt' command to stop the monitoring
                # and processing.
                dataq.put('all_data')
                notifier.stop()
                interrupted = True
                break
            else:
                fp, tags = utils.get_data_hd5(file)
                data_tag = tags['/exchange/'+data_type]
                data = np.asarray(fp[data_tag])
                slice_index += data.shape[0]
                file_indexes[file] = slice_index
                for i in range(0, data.shape[0]):
                    dataq.put(Data(data[i]))
                file_index += 1
                if file_index == num_files:
                    dataq.put('all_data')
                    notifier.stop()
                    interrupted = True
                    break

    aggregate = aggregateq.get()

    report_file = None
    try:
        report_file_name = conf['report_file']
        try:
            report_file = open(report_file_name, 'w')
        except:
            logger.warning ('Cannot open report file, writing report to console')
    except KeyError:
        logger.warning ('report file not configured, writing report to console')
        pass

    report.report_results(aggregate, data_type, report_file)
    bad_indexes = {}
    if report_by_files:
        report.add_bad_indexes_per_file(aggregate, data_type, bad_indexes, file_indexes)
    else:
        report.add_bad_indexes(aggregate, data_type, bad_indexes)
    report.report_bad_indexes(bad_indexes, report_file)

    return bad_indexes


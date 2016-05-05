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
from multiprocessing import Queue
import json
import dquality.common.utilities as utils
import dquality.common.report as report
import dquality.data as dataver

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

    extensions : list
        a list containing extensions of files to be monitored read from the configuration file
    """
    conf = utils.get_config(config)

    logger = utils.get_logger(__name__, conf)

    dir = utils.get_directory(conf, logger)
    if dir is None:
        sys.exit(-1)

    limitsfile = utils.get_file(conf, 'limits', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())['limits']

    report_file = utils.get_file(conf, 'report_file', logger)

    extensions = conf['extensions']

    return logger, limits, report_file, extensions


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
        Directory to monitor

    patterns : list
        A list of strings representing file extension. Closing matching files will generate
        event.

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

def verify(conf, folder, num_files):
    """
    This is the main function called when the verifier application starts.
    The configuration and the directory to monitor are passed as parameters,
    as well as number of files that will be accepted. If the files to
    monitor for should have certain extension, a list of acceptable
    file extensions can be defined in a configuration file.

    The function calls directory function that sets up the monitoring
    and returns notifier. After the monitoring is initialized, it starts
    a loop that reads the global "*files*" queue. If there is any new file,
    the file is removed and validate with data.verify function.

    The loop is interrupted when all expected files produced results.

    Parameters
    ----------
    conf : str
        configuration file name including path

    folder : str
        folder name to monitor

    num_files : int
        expected number of files. This script will exit after detecting and
        processing given number of files.

    Returns
    -------
    None
    """
    logger, limits, report_file, extensions = init(conf)
    if not os.path.isdir(folder):
        logger.error(
            'parameter error: directory ' +
            folder + ' does not exist')
        sys.exit(-1)

    try:
        notifier = directory(folder, extensions)
    except KeyError:
        logger.warning('no file extension specified. Monitoring for all files.')
        notifier = directory(folder, None)

    bad_indexes = {}
    file_count = 0
    interrupted = False

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
            print ('file', file)
            if file == INTERRUPT:
                # the calling function may use a 'interrupt' command to stop the monitoring
                # and processing.
                notifier.stop()
                interrupted = True
                break
            else:
                file_count += 1
                bad_indexes[file] = dataver.verify_file(logger, file, limits, None)
                print (bad_indexes.keys())
        if file_count == num_files:
            print ('file_count, num_files',file_count, num_files)
            interrupted = True

    if report_file is not None:
        try:
            report_file = open(report_file, 'w')
        except:
            logger.warning('Cannot open report file, writing report on console')
            report_file = None

    report.report_bad_indexes(bad_indexes, report_file)

    return bad_indexes


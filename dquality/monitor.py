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
import dquality.common.constants as const
import dquality.data as dataver
import glob


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

    data_tags : dict
        a dictionary od data_type/hdf tag

    limits : dictionary
        a dictionary containing limit values read from the configured 'limit' file

    quality_checks : dict
        a dictionary containing quality check functions ids

    extensions : list
        a list containing extensions of files to be monitored read from the configuration file

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

    return logger, data_tags, limits, quality_checks, extensions, file_type, report_type, report_dir, consumers


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
    notifier : Notifier
        an instance of Notifier
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
    This function discovers new files and evaluates data in the files.

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
        folder name to monitor, if the level 1 subdirectories are to be monitored, add '/**'
        to the folder

    num_files : int
        expected number of files. This script will exit after detecting and
        processing given number of files.

    Returns
    -------
    bad_indexes : Dict
        A dictionary containing indexes of slices that did not pass quality check. The key is a file.

    """
    logger, data_tags, limits, quality_checks, extensions, file_type, report_type, report_dir, consumers = init(conf)
    if folder.endswith('**'):
        check_folder = folder[0:-2]
    else:
        check_folder = folder
    if not os.path.isdir(check_folder):
        logger.error(
            'parameter error: directory ' +
            folder + ' does not exist')
        sys.exit(-1)

    paths = glob.glob(folder)
    notifiers = []
    for dir in paths:
        notifiers.append(directory(dir, extensions))

    bad_indexes = {}
    file_count = 0
    interrupted = False

    while not interrupted:
        # The notifier will put a new file into a newFiles queue if one was
        # detected
        for notifier in notifiers:
            notifier.process_events()
            if notifier.check_events(timeout=0.5):
                notifier.read_events()

        # checking the newFiles queue for new entries and starting verification
        # processes for each new file
        while not files.empty():
            file = files.get()
            if file.find('INTERRUPT') >= 0:
                # the calling function may use a 'interrupt' command to stop the monitoring
                # and processing.
                for notifier in notifiers:
                    notifier.stop()
                interrupted = True
                break
            else:
                file_count += 1
                if file_type == const.FILE_TYPE_GE:
                    bad_indexes[file] = dataver.verify_file_ge(logger, file, limits, quality_checks, report_type, report_dir, consumers)
                else:
                    bad_indexes[file] = dataver.verify_file_hdf(logger, file, data_tags, limits, quality_checks, report_type, report_dir, consumers)
                print (file)
                print ('bad indexes: ', bad_indexes[file])
                logger.info('monitor evaluated ' + file + ' file')

        if file_count == num_files:
            notifier.stop()
            interrupted = True

    return bad_indexes


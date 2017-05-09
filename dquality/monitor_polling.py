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
from multiprocessing import Queue
import json
import dquality.common.utilities as utils
import dquality.common.constants as const
import dquality.data as dataver
from threading import Timer
import stat


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'verify']

INTERRUPT = 'interrupt'


class FileSeek():
    """
    This class provides file discovery functionality.

    An instance is initialized with parameters.
    On the start the FileSeek checks for existing files. After that it periodically checks
    for new files in monitored directory and subdirectories. Upon finding a new or updated file it
    velidates the file and enqueues into the queue on success.
    """

    def __init__(self, q, polling_period, logger, file_type):
        """
        constructor

        Parameters
        ----------
        q : Queue
            a queue used to pass discovered files

        polling_period : int
            number of second defining polling period

        logger : Logger
            logger instance

        file_type : int
            a constant defining type of data file. Supporting FILE_TYPE_GE and FILE_TYPE_HDF
        """
        self.q = q
        self.polling_period = polling_period
        self.processed_files = None
        self.logger = logger
        self.file_type = file_type
        self.done = False

    def get_files(self, folder, ext, discovered_files=None):
        """
        Finds files in a given directory and subdirectories.

        Parameters
        ----------
        folder : str
            a folder name that will be checked for files

        ext : list
            list of file extensions that will be discovered

        discovered_files : dict
            a dictionary to add the discovered files to

        Returns
        -------
        dict
            a dictionary with keys as files in a monitored folder and subdirectories
        """

        current_files = discovered_files
        if current_files is None:
            current_files = {}
        if os.path.isdir(folder):
            files = os.listdir(folder)
            for f in files:
                full_path = os.path.join(folder, f)
                if os.path.isfile(full_path):
                    match = False
                    for fext in ext:
                        if f.endswith(fext):
                            match = True
                    if match:
                        statResult = os.stat(full_path)
                        file_info = {}
                        file_info['fileSize'] = statResult[stat.ST_SIZE]
                        file_info['fileModificationTime'] = statResult[stat.ST_MTIME]
                        current_files[full_path] = file_info
                elif os.path.isdir(full_path):
                    current_files = self.get_files(full_path, ext, current_files)
        return current_files

    def notify(self, file_name):
        """
        This method performs action to notify stakeholders about a discovered file.

        Currently the notification is done by using queue.
        This method validates the file first. If file validated successfully, the full file name is enqueued.
        The file might not validate if has been discovered before it is complete. In such situation, the file will
        be discovered again when updated.

        Parameters
        ----------
        file_name : str
            a full name of a file

        Returns
        -------
        none
        """

        if self.file_type == const.FILE_TYPE_GE:
            validator = FileValidatorGe()
            if validator.is_valid(file_name):
                self.q.put(file_name)
        else:
            # the velidator is not implemented, so for now pass all discovered files
            self.q.put(file_name)

    def process_files(self, previous_files, current_files):
        """
        This method compares new latest discovered files with previously found files. The new files are reported
        through notify to the stakeholders.

        Parameters
        ----------
        previous_files : dict
            a dictionary of previously found files

        current_files : dict
            a dictionary of currently found files

        Returns
        -------
        none
        """

        for file_name in current_files.keys():
            if not file_name in previous_files:
                # new file, must be updated
                self.notify(file_name)
            else:
                # old file, check timestamp
                prev_file_info = previous_files.get(file_name)
                prev_modification_time = prev_file_info.get('fileModificationTime', '')
                file_info = current_files.get(file_name)
                modification_time = file_info.get('fileModificationTime')
                if modification_time != prev_modification_time:
                    # file has been modified, need to process it
                    self.notify(file_name)


    def poll_file_system(self, folder, ext):
        """
        This method initiates for polling the file information off of the file system.

        Parameters
        ----------
        folder : str
            a folder name that will be checked for files

        ext : list
            list of file extensions that will be discovered

        discovered_files : dict
            a dictionary to add the discovered files to

        Returns
        -------
        none
        """

        try:
            current_files = self.get_files(folder, ext)
            self.process_files(self.processed_files, current_files)
            self.processed_files = current_files
        except:
            self.logger.error('Could not poll directory %s' % (folder))
        self.start_observing(folder, ext)

    def start_observing(self, folder, ext):
        """
        This method startss for polling the file information off of the file system.

        Parameters
        ----------
        folder : str
            a folder name that will be checked for files

        ext : list
            list of file extensions that will be discovered

        discovered_files : dict
            a dictionary to add the discovered files to

        Returns
        -------
        none
        """

        if self.processed_files is None:
            self.processed_files = self.get_files(folder, ext)
        if self.done:
            return

        t = Timer(self.polling_period, self.poll_file_system, [folder, ext])
        self.t = t
        t.start()

    def stop_observing(self):
        """
        This method stops the polling the file information off of the file system.

        Parameters
        ----------
        none

        Returns
        -------
        none
        """

        self.t.cancel()
        self.done = True


class FileValidatorGe():
    """
    This class is an interface to the concrete file verification functionality.
    """
    def is_valid(self, file):
        """
        This method checks if the ge file is compatible with the standards.

        Parameters
        ----------
        file : str
            file name

        Returns
        -------
        True if validated, False otherwise
        """

        import struct as st

        fp = open(file, 'rb')
        offset = 8192

        fp.seek(18)
        size, nframes = st.unpack('<ih',fp.read(6))
        if size != 2048:
            return False

        fsize = os.stat(str(fp).split("'")[1]).st_size
        nframes_calc = (fsize - offset)/(2*size**2)

        if nframes != nframes_calc:
            return False

        return True


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


def verify(conf, folder, num_files):
    """
    This function discovers new files and evaluates data in the files.

    This is the main function called when the verifier application starts.
    The configuration and the directory to monitor are passed as parameters,
    as well as number of files that will be accepted. If the files to
    monitor for should have certain extension, a list of acceptable
    file extensions can be defined in a configuration file.

    The function sets up the monitoring and starts
    a loop that reads the "*files*" queue. If there is any new file,
    the file is dequeued and validated with data.verify function.

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
    if not os.path.isdir(folder):
        logger.error('parameter error: directory ' + folder + ' does not exist')
        sys.exit(-1)
    filesq = Queue()

    # create notifier that will poll file system every 1 second for new files
    notifier = FileSeek(filesq, 1, logger, file_type)
    notifier.start_observing(folder, extensions)
    bad_indexes = {}
    file_count = 0
    interrupted = False

    while not interrupted:
        # checking the newFiles queue for new entries and starting verification
        # processes for each new file
        while not filesq.empty():
            file = filesq.get()
            if file.find('INTERRUPT') >= 0:
                # the calling function may use a 'interrupt' command to stop the monitoring
                # and processing.
                interrupted = True
                notifier.stop_observing()
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
            interrupted = True
            notifier.stop_observing()

    return bad_indexes


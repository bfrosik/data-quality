#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2015, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2015. UChicago Argonne, LLC. This software was produced       #
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
This module requires the "*definitions for verifier*" section of `config.ini <https://github.com/bfrosik/data-quality/blob/master/dquality/config.ini>`__ file to be set.

The application monitors given directory for new/modified files of the given pattern.
Each of the detected file is verified according to schema configuration and for each of the file several new processes
are started, each process performing specific quality calculations.

The results will be sent to an EPICS PV (printed on screen for now).

"""

import h5py
import os
import sys
from multiprocessing import Process, Queue
import pyinotify
from pyinotify import WatchManager
from configobj import ConfigObj

from pvverifier import verify_pv
from structureverifier import structure
from common.qualitychecks import Data, validate_mean_signal_intensity, validate_signal_intensity_standard_deviation, \
    validate_voxel_based_SNR, validate_slice_based_SNR
from common.utilities import get_data


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['verify_live',
           'verify_data_quality',
           'monitor_dir',
           'cleanup']

config = ConfigObj('config.ini')
processes = {}
files = Queue()
results = Queue()
interrupted = False
INTERRUPT = 'interrupt'

def verify_data_quality(file, function, process_id):
    """
    This method creates a new process that is associated with the "*function*" parameter.
    The created process is stored in global "*processes*" dictionary with the key "*process_id*" parameter.
    The process is started.
     
    Parameters
    ----------
    file : str
        File Name including path
    
    function : function
        Function that will be executed when process starts.

    process_id : int
        Unique process id assigned by calling method
        
    Returns
    -------
    None        
    """
    print function
    p = Process(target=function, args=(file, process_id, results,))
    processes[process_id] = p
    p.start()

def monitor_dir(directory, patterns):
    """
    This method monitors a directory given by the "*directory*" parameter.
    It creates a notifier object. The notifier is registered to await the "*CLOSE_WRITE*" event on a new file
    that matches the "*pattern*" parameter. If there is no such event, it yields control on timeout, defaulted to 1 second.
    It returns the created notifier.
     
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
            for pattern in patterns.as_list('extensions'):
                file = event.pathname
                if file.endswith(pattern):
                    # before any data verification check the data structure against given schema
                    if structure(file):
                        files.put(event.pathname)
                        break
                    else:
                        files.put(INTERRUPT)
                        break

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler, timeout=1)
    wdd = wm.add_watch(directory, mask, rec=False)
    return notifier

def cleanup():
    """
    This method is called on exit. If any process is still active it will be terminated.
     
    Parameters
    ----------
    None
        
    Returns
    -------
    None        
    """
    for process in processes.itervalues():
        process.terminate()
        notifier.stop()

def verify_live():
    """
    This is the main function called when the verifier application starts.
    It reads the configuration for the directory to monitor, for pattern that represents a file extension to look for, 
    and for a number of files that are expected for the experiment. 
    The number of files configuration parameter is added for experiments that generate multiple files.
    In some cases the experiment data is collected into a single file, which is organized with data sets.
    
    The function calls monitor_dir function that sets up the monitoring and returns notifier.
    After the monitoring is initialized, it starts a loop that reads the global "*files*" queue and then the global "*results*" queue.
    If there is any new file, the file is removed from the queue, and the data in the file is validated by a sequence of validation
    methods.
    If there is any new result, the result is removed from the queue, corresponding process is terminated, and the result is 
    presented. (currently printed on console, later will be pushed into an EPICS process variable)
    
    The loop is interrupted when all expected processes produced results. The number of expected processes is determined by
    number of files and number of validation functions.
    
     
    Parameters
    ----------
    None

    Returns
    -------
    None        
    """
    if not verify_pv():
        # the function willl print report if error found
        sys.exit(-1)
        
    numberverifiers = 2 # number of verification functions to call for each data file
    process_id = 0
    #The verifier can be configured to verify file or to monitor a directory and verify a new file on close save.
    try:
        # check if directory exists
        directory = config['directory']
        if not os.path.isdir(directory):
            print ('configuration error: directory ' + directory + ' does not exist')
            sys.exit()
        notifier = monitor_dir(directory, config['file_patterns'])
        numresults = int(config['number_files']) * numberverifiers
    except KeyError:
        print ('config error: directory not configured')
        sys.exit(-1)

    while not interrupted:
        # The notifier will put a new file into a newFiles queue if one was detected
        notifier.process_events()
        if notifier.check_events():
             notifier.read_events()

        # checking the newFiles queue for new entries and starting verification processes for each new file
        while not files.empty():
            file = files.get()
            if file == INTERRUPT:
                # the schema verification may detect incorrect file structure and thus request to exit.
                interrupted = True
            else:
                data = Data(file, get_data(file))
                process_id = process_id + 1
                verify_data_quality(data, validate_mean_signal_intensity, process_id)
                process_id = process_id + 1
                verify_data_quality(data, validate_signal_intensity_standard_deviation, process_id)

        # checking the result queue and printing result
        # later the result will be passed to an EPICS process variable
        while not results.empty():
            res = results.get()
            pr = processes[res.process_id]
            pr.terminate()
            del processes[res.process_id]
            numresults = numresults -1
            print ('result: file name, result, quality id, error: ', res.file, res.res, res.quality_id, res.error)

        if numresults is 0:
            interrupted = True

    cleanup()
    print ('finished')


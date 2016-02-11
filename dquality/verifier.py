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
This application assumes there is a 'config.ini' file that contains parameters required to run the application:

'directory' - directory that will be monitored
'file_pattern' - a file extension (i.e 'hd5' or 'txt')
'number_files' - number of files expected to be collected for the experiment

The application monitors given directory for new/modified files of the given pattern.
For each of detected file several new processes are started, each process performing specific quality calculations.

The results will be sent to an EPICS PV (printed on screen for now)
"""

from multiprocessing import Process, Queue
import time
import pyinotify
from pyinotify import WatchManager
from configobj import ConfigObj

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['validateMeansignalIntensity',
           'validateSignalIntensityStandardDeviation',
           'verifyFileQuality',
           'monitorDir']

config = ConfigObj('config.ini')
processes = {}
newFiles = Queue()
resultsQueue = Queue()
interrupted = False

class result:
    def __init__(self, file, res, process_id, quality_id, error):
        self.file = file
        self.res = res
        self.process_id = process_id
        self.quality_id = quality_id
        self.error = error

def validateMeansignalIntensity(file, process_id):
    #do calculations, and obtain quality
    quality_id = 1
    quality = 7.0
    #error = quality > 10.2
    error = False
    result1 = result(file, quality, process_id, quality_id, error)
    time.sleep(10)
    resultsQueue.put(result1)

def validateSignalIntensityStandardDeviation(file, process_id):
    #do calculations, and obtain quality
    quality = 3
    quality_id = 2
    #error = quality < 4
    error = False
    result2 = result(file, quality, process_id, quality_id, error)
    time.sleep(10)
    resultsQueue.put(result2)

def verifyFileQuality(file, function, process_id):
    p = Process(target=function, args=(file, process_id,))
    processes[process_id] = p
    p.start()

def monitorDir(directory, pattern):
    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CLOSE_WRITE(self, event):
            if event.pathname.endswith(pattern):
                newFiles.put(event.pathname)

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler, timeout=1)
    wdd = wm.add_watch(directory, mask, rec=False)
    return notifier

if __name__ == '__main__':
    numberverifiers = 2 # number of verification functions to call for each data file
    process_id = 0
    notifier = monitorDir(config['directory'], config['file_pattern'])
    numExpectedResults = int(config['number_files']) * numberverifiers
    while not interrupted:

        # The notifier will put a new file into a newFiles queue if one was detected
        notifier.process_events()
        if notifier.check_events():
            notifier.read_events()

        # checking the newFiles queue for new entries and starting verification processes for each new file
        while not newFiles.empty():
            newFile = newFiles.get()
            process_id = process_id + 1
            verifyFileQuality(newFile, validateMeansignalIntensity, process_id)
            process_id = process_id + 1
            verifyFileQuality(newFile, validateSignalIntensityStandardDeviation, process_id)

        # checking the result queue and printing result
        # later the result will be passed to an EPICS process variable
        while not resultsQueue.empty():
            res = resultsQueue.get()
            pr = processes[res.process_id]
            pr.terminate()
            del processes[res.process_id]
            numExpectedResults = numExpectedResults -1
            print ('result: file name, result, quality id, error: ', res.file, res.res, res.quality_id, res.error)
            if res.error:
                interrupted = True

        if numExpectedResults is 0:
            interrupted = True

    notifier.stop()


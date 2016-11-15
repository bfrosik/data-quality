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

This module feeds the data coming from detector to a process using queue. It interracts with a channel access
plug in of area detector. The read of frame data from channel access happens on event of frame counter change.
The change is detected with a callback. The data is passed to the consuming process.
This module requires configuration file with the following parameters:
'detector', a string defining the first prefix in area detector, it has to match the area detector configuration
'detector_basic', a string defining the second prefix in area detector, defining the basic parameters, it has to
match the area detector configuration
'detector_image', a string defining the second prefix in area detector, defining the image parameters, it has to
match the area detector configuration
'no_frames', number of frames that will be fed
'args', optional, list of process specific parameters, they need to be parsed to the desired format in the wrapper
"""

from epics import caget, PV
from epics.ca import CAThread
from multiprocessing import Queue
import numpy as np
from adapter import start_process, parse_config, pack_data
import sys
if sys.version[0] == '2':
    import Queue as tqueue
else:
    import queue as tqueue



__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['deliver_data',
           'on_change',
           'start_processes',
           'get_pvs',
           'feed_data']

class Shared:
     """
     This class contains the global variables shared between threads.
     """
     def __init__(self, ):
         self.process_dataq = Queue()
         self.exitq = tqueue.Queue()
         self.thread_dataq = tqueue.Queue()
         self.sizex = 0
         self.sizey = 0
         self.no_frames = 0
         self.ctr = 0

globals = Shared()

# class Data:
#      def __init__(self, slice,):
#          self.slice = slice
#

def deliver_data(data_pv, logger):
    """
    This function is invoked at the beginning of the feed as a distinct thread. It reads data from a queue inside a loop.
    It loops until all frames are processed, which is marked by 'missing' string, or if an error occurs. The data
    retrieved from the queue is the frame counter number that was discovered in the callback method.
    The counter is compared with a previous counter value. If the gap between the two is greater than 1, then frame(s)
    have been missing. For each missing frame a 'missing' string is enqueued into the inter-process queue. The frame
    is polled from the channel access and enqueued into the inter-process queue.
    At the loop exit an 'all_data' string is enqueud into the inter-process queue, and 'exit' string is enqueued
    into the inter-thread queue, to notify the main thread of an exit event.

    Parameters
    ----------
    data_pv : str
        a PV string for the area detector data

    logger : Logger
        a Logger instance, typically synchronized with the consuming process logger

    Returns
    -------
    None
    """

    def finish():
        globals.process_dataq.put('all_data')
        globals.exitq.put('exit')

    done = False
    while not done:
        current_counter = globals.thread_dataq.get()
        if current_counter < globals.no_frames:
            try:
                data = np.array(caget(data_pv))
            except:
                finish()
                done = True
                logger.error('reading image raises exception, possibly the detector exposure time is too small')
            if data is None:
                finish()
                done = True
                logger.error('reading image times out, possibly the detector exposure time is too small')
            else:
                delta = current_counter - globals.ctr
                globals.ctr = current_counter
                data.resize(globals.sizex, globals.sizey)
                if delta > 1:
                    for i in range (1, delta):
                        globals.process_dataq.put('missing')
                globals.process_dataq.put(pack_data(data))
        else:
            finish()
            done = True


def on_change(pvname=None, **kws):
    """
    A callback method that activates when a frame counter of area detector changes. This method reads the counter
    value and enqueues it into inter-thread queue that will be dequeued by the 'deliver_data' function.
    If it is a first read, the function adjusts counter data in the globals object.

    Parameters
    ----------
    pvname : str
        a PV string for the area detector frame counter

    Returns
    -------
    None
    """

    current_ctr = kws['value']
    #on first callback adjust the values
    if globals.ctr == 0:
        globals.no_frames += current_ctr
        globals.ctr = current_ctr

    globals.thread_dataq.put(current_ctr)


def start_processes(counter_pv, data_pv, logger, *args):
    """
    This is a main thread that starts thread reacting to the callback, starts the consuming process, and sets a
    callback on the frame counter PV change. The function then awaits for the data in the exit queue that indicates
    that all frames have been processed. The functin cancells the callback on exit.

    Parameters
    ----------
    counter_pv : str
        a PV string for the area detector frame counter

    data_pv : str
        a PV string for the area detector frame data

    logger : Logger
        a Logger instance, typically synchronized with the consuming process logger

    *args : list
        a list of arguments specific to the client process

    Returns
    -------
    None
    """
    data_thread = CAThread(target = deliver_data, args=(data_pv, logger,))
    data_thread.start()

    start_process(globals.process_dataq, logger, *args)
    cntr = PV(counter_pv)
    cntr.add_callback(on_change, index = 1)

    globals.exitq.get()
    cntr.clear_callbacks()


def get_pvs(detector, detector_basic, detector_image):
    """
    This function takes defined strings from configuration file and constructs PV variables that are accessed during
    processing.

    Parameters
    ----------
    detector : str
        a string defining the first prefix in area detector, it has to match the area detector configuration

    detector_basic : str
        a string defining the second prefix in area detector, defining the basic parameters, it has to
        match the area detector configuration

    detector_image : str
        a string defining the second prefix in area detector, defining the image parameters, it has to
        match the area detector configuration

    Returns
    -------
    acquire_pv : str
        a PV string representing acquireing state

    counter_ pv : str
        a PV string representing frame counter

    data_pv : str
        a PV string representing acquired data

    sizex_pv : str
        a PV string representing x size of acquired data

    sizey_pv : str
        a PV string representing y size of acquired data
    """

    acquire_pv = detector + ':' + detector_basic + ':' + 'Acquire'
    counter_pv = detector + ':' + detector_basic + ':' + 'NumImagesCounter_RBV'
    data_pv = detector + ':' + detector_image + ':' + 'ArrayData'
    sizex_pv = detector + ':' + detector_image + ':' + 'ArraySize0_RBV'
    sizey_pv = detector + ':' + detector_image + ':' + 'ArraySize1_RBV'
    return acquire_pv, counter_pv, data_pv, sizex_pv, sizey_pv


def feed_data(config, logger, *args):
    """
    This function is called by an client to start the process. It parses configuration and gets needed process
    variables. It stores necessary values in the globals object.
    After all initial settings are completed, the method awaits for the area detector to start acquireing by polling
    the PV. When the area detective is active it starts processing.

    Parameters
    ----------
    config : str
        a configuration file

    logger : Logger
        a Logger instance, recommended to use the same logger for feed and consuming process

    *args : list
        a list of process specific arguments

    Returns
    -------
    None
    """

    no_frames, detector, detector_basic, detector_image = parse_config(config)
    acquire_pv, counter_pv, data_pv, sizex_pv, sizey_pv = get_pvs(detector, detector_basic, detector_image)
    globals.no_frames = no_frames
    test = True
    while test:
        globals.sizex = caget (sizex_pv)
        globals.sizey = caget (sizey_pv)
        ack =  caget(acquire_pv)
        if ack == 1:
            test = False
            start_processes(counter_pv, data_pv, logger, *args)



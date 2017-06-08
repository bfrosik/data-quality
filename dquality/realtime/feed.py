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
The change is detected with a callback. The data type is determined from PV. The data and the type are passed
(as object) to the consuming process.
This module requires configuration file with the following parameters:
'detector', a string defining the first prefix in area detector, it has to match the area detector configuration
'detector_basic', a string defining the second prefix in area detector, defining the basic parameters, it has to
match the area detector configuration
'detector_image', a string defining the second prefix in area detector, defining the image parameters, it has to
match the area detector configuration
'no_frames', number of frames that will be fed. If not given, the optional parameter 'sequence' to the feed_data
method must not be None. It can be either int defining number of frames, or a list of touples, defining data types
sequence. (i.e. [('data_dark', 4), ('data_white', 14), ('data', 614), ('data_dark', 619))
'args', optional, list of process specific parameters, they need to be parsed to the desired format in the wrapper
"""

from epics import caget, PV
from epics.ca import CAThread
from multiprocessing import Queue
import numpy as np
import dquality.realtime.adapter as adapter
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

class Feed:
    """
    This class reads frames in a real time using pyepics, and delivers to consuming process.
    """
    def __init__(self):
        """
        Constructor

        This constructor creates the following queues:
        process_dataq : a queue used to pass data to the consuming process
        exitq : a queue used to signal awaiting process the end of processing, so the resources can be closed
        thread_dataq : this queue delivers counter number on change from call back thread
        Other fields are initialized.
        """
        self.process_dataq = Queue()
        self.exitq = tqueue.Queue()
        self.thread_dataq = tqueue.Queue()
        self.sizex = 0
        self.sizey = 0
        self.no_frames = 0
        self.ctr = 0
        self.sequence = None
        self.sequence_index = 0
        self.cntr_pv = None


    def deliver_data(self, data_pv, frame_type_pv, logger):
        """
        This function receives data, processes it, and delivers to consuming process.

        This function is invoked at the beginning of the feed as a distinct thread. It reads data from a thread_dataq
        inside a loop that delivers current counter value on change.
        If the counter is not a consecutive number to the previous reading a 'missing' string is enqueued into
        process_dataq in place of the data to mark the missing frames.
        For every received frame data, it reads a data type from PV, and the two elements are delivered to a consuming
        process via process_dataq as Data instance. If a sequence is defined, then the data type for this frame
        determined from sequence is compared with the data type read from PV. If they are different, a warning log is
        recorded.
        On the loop exit an 'all_data' string is enqueud into the inter-process queue, and 'exit' string is enqueued
        into the inter-thread queue, to notify the main thread of the exit event.
    
        Parameters
        ----------
        data_pv : str
            a PV string for the area detector data

        frame_type_pv : str
            a PV string for the area detector data type
    
        logger : Logger
            a Logger instance, typically synchronized with the consuming process logger
    
        Returns
        -------
        None
        """
        def build_type_map():
            types = {}
            types[0] = 'data'
            types[1] = 'data_dark'
            types[2] = 'data_white'
            types[3] = 'data' # it'd double correlation, but leave data for now
            return types

        def verify_sequence(logger, data_type):
            while frame_index > self.sequence[self.sequence_index][1]:
                self.sequence_index += 1
            planned_data_type = self.sequence[self.sequence_index][0]
            if planned_data_type != data_type:
                logger.warning('The data type for frame number ' + str(frame_index) + ' is ' + data_type + ' but was planned ' + planned_data_type)

        # def finish():
        #     self.process_dataq.put(pack_data(None, "end"))
        #     self.exitq.put('exit')

        types =  build_type_map()
        done = False
        frame_index = 0
        while not done:
            current_counter = self.thread_dataq.get()
            if self.no_frames < 0 or current_counter < self.no_frames:
                try:
                    data = np.array(caget(data_pv))
                    data_type = types[caget(frame_type_pv)]
                    if data is None:
                        self.finish()
                        done = True
                        logger.error('reading image times out, possibly the detector exposure time is too small')
                    else:
                        delta = current_counter - self.ctr
                        self.ctr = current_counter
                        data.resize(self.sizex, self.sizey)
                        if delta > 1:
                            for i in range (1, delta):
                                self.process_dataq.put(adapter.pack_data(None, "missing"))
                        frame_index += delta
                        packed_data = self.get_packed_data(data, data_type)
                        self.process_dataq.put(packed_data)
                        if self.sequence is not None:
                            verify_sequence(logger, data_type)
                except:
                    self.finish()
                    done = True
                    logger.error('reading image raises exception, possibly the detector exposure time is too small')
            else:
                done = True

        self.finish()

    def get_packed_data(self, data, data_type):
        return adapter.pack_data(data, data_type)
    
    def on_change(self, pvname=None, **kws):
        """
        A callback method that activates when a frame counter of area detector changes.

        This method reads the counter value and enqueues it into inter-thread queue that will be dequeued by the
        'deliver_data' function.
        If it is a first read, the function adjusts counter data in the self object.
    
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
        if self.ctr == 0:
            self.ctr = current_ctr
            if self.no_frames >= 0:
                self.no_frames += current_ctr

        self.thread_dataq.put(current_ctr)
    
    
    def start_processes(self, counter_pv, data_pv, frame_type_pv, logger, *args):
        """
        This function starts processes and callbacks.

        This is a main thread that starts thread reacting to the callback, starts the consuming process, and sets a
        callback on the frame counter PV change. The function then awaits for the data in the exit queue that indicates
        that all frames have been processed. The functin cancells the callback on exit.
    
        Parameters
        ----------
        counter_pv : str
            a PV string for the area detector frame counter
    
        data_pv : str
            a PV string for the area detector frame data

        frame_type_pv : str
            a PV string for the area detector data type
    
        logger : Logger
            a Logger instance, typically synchronized with the consuming process logger
    
        *args : list
            a list of arguments specific to the client process
    
        Returns
        -------
        None
        """
        data_thread = CAThread(target = self.deliver_data, args=(data_pv, frame_type_pv, logger,))
        data_thread.start()

        adapter.start_process(self.process_dataq, logger, *args)
        self.cntr_pv = PV(counter_pv)
        self.cntr_pv.add_callback(self.on_change, index = 1)
    
        # self.exitq.get()
        # print 'got Exit in exitq stopping callback'
        # self.cntr.clear_callbacks()
    
    
    def get_pvs(self, detector, detector_basic, detector_image):
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

        frame_type_pv : str
            a PV string for the area detector data type

        """
    
        acquire_pv = detector + ':' + detector_basic + ':' + 'Acquire'
        counter_pv = detector + ':' + detector_basic + ':' + 'NumImagesCounter_RBV'
        data_pv = detector + ':' + detector_image + ':' + 'ArrayData'
        sizex_pv = detector + ':' + detector_image + ':' + 'ArraySize0_RBV'
        sizey_pv = detector + ':' + detector_image + ':' + 'ArraySize1_RBV'
        frame_type_pv = detector + ':' + detector_basic + ':' + 'FrameType'
        return acquire_pv, counter_pv, data_pv, sizex_pv, sizey_pv, frame_type_pv
    
    
    def feed_data(self, no_frames, detector, detector_basic, detector_image, logger, sequence=None, *args):
        """
        This function is called by an client to start the process.

        It parses configuration and gets needed process variables. It stores necessary values in the self object.
        After all initial settings are completed, the method awaits for the area detector to start acquireing by polling
        the PV. When the area detective is active it starts processing.
    
        Parameters
        ----------
        config : str
            a configuration file
    
        logger : Logger
            a Logger instance, recommended to use the same logger for feed and consuming process

        sequence : list or int
            if int, the number is used to set number of frames to process,
            if list, take the number of frames from the list, and verify the sequence of data is correct during
            processing
    
        *args : list
            a list of process specific arguments
    
        Returns
        -------
        None
        """
        acquire_pv, counter_pv, data_pv, sizex_pv, sizey_pv, frame_type_pv = self.get_pvs(detector, detector_basic, detector_image)
        self.no_frames = no_frames
        # if sequence is None:
        #     self.no_frames = no_frames
        # elif type(sequence) is int:
        #     self.no_frames = sequence
        # else:
        #     self.sequence = sequence
        #     self.no_frames = sequence[len(sequence)-1][1] + 1

        test = True

        while test:
            self.sizex = caget (sizex_pv)
            self.sizey = caget (sizey_pv)
            ack =  caget(acquire_pv)
            if ack == 1:
                test = False
                self.start_processes(counter_pv, data_pv, frame_type_pv, logger, *args)

        return caget(acquire_pv)


    def finish(self):
        self.process_dataq.put(adapter.pack_data(None, "end"))
        self.cntr_pv.clear_callbacks()


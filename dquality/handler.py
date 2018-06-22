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

This handler modules receives data, calls quality check processes to verify the data,
and handles results of the checks.

"""

import dquality.common.constants as const
import dquality.common.qualitychecks as calc
from dquality.common.containers import Aggregate
import dquality.clients.zmq_client as cons
import sys
from collections import deque
if sys.version[0] == '2':
    import Queue as queue
else:
    import queue as queue

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init_consumers',
           'send_to_consumers',
           'handle_data']


def init_consumers(consumers):
    """
    This function starts consumer processes.

    It reads consumer processes parameters from the 'consumers' dictionary, adds installation directory to the path for
    each consumer process, and starts the processes with retrieved arguments.

    Parameters
    ----------
    consumers : dict
        a dictionary containing consumer processes to run, and their parameters

    Returns
    -------
    consumers_q : list
        a list of Queues that are used to deliver frames to consumers
    """

    consumer_zmq = []
    # connect to one consumer, may be extended to many later
    zmq_sender = cons.zmq_sen(str(consumers))
    consumer_zmq.append(zmq_sender)

    return consumer_zmq


def send_to_consumers(consumer_zmq, data, results):
    """
    This function receives frames in a real time and delivers them to the consumer processes.

    It reads consumer processes parameters from the 'consumers' dictionary, adds installation directory to the path for
    each consumer process, and starts the processes with retrieved arguments.

    Parameters
    ----------
    waiting_q : deque
        an instance of collection.deque used to pass frames and the results

    consumer_q : list
        a list of Queues on which the frames are delivered to consumers

    results : Results
       a Results container that holds results for the frame

    Returns
    -------
    none
    """
    if not consumer_zmq is None:
        # for consumer in consumer_zmq:
        #     consumer.send_to_zmq(data, results)
        if data.status == const.DATA_STATUS_DATA:
            data.ver = not results.failed
            data.image_number = results.index
            for consumer in consumer_zmq:
                consumer.send_to_zmq(data)


def handle_data(dataq, reportq, args, kwargs):
    """
    This function creates and initializes all variables and handles data received on a 'dataq' queue.

    This function is typically called as a new process. It takes a dataq parameter
    that is the queue on which data is received. It takes the dictionary containing limit values
    for the data type being processed, such as data_dark, data_white, or data.
    It takes a reportq parameter, a queue, which is used to report results.
    The quality_checks is a dictionary, where the keys are quality checks methods ids (constants defined in
    dquality.common.constants) and values are lislts of statistical quality check methods ids that use results from the
    method defined as a key.

    The initialization constrains of creating aggregate instance to track results for a data type,
    queue for quality checks results passing, queue for statistical quality checks results passing,
    and initializing variables.

    This function has a loop that retrieves data from the data queue, runs a sequence of
    validation methods on the data, and retrieves results from the results queues.
    Each result object contains information whether the data was out of limits, in addition
    to the value and index. Each result is additionally evaluated with relation to the previously
    accumulated results.

    The loop is interrupted when the data queue received end of data element, and all
    processes produced results.


    Parameters
    ----------
    dataq : Queue
        data queuel; data is received in this queue

    limits : dictionary
        a dictionary of limits for the processed data type

    reportq : Queue
        results queue; used to pass results to the calling process

    quality_checks : dict
        a dictionary by data type of quelity check dictionaries:
        keys are ids of the basic quality check methods, and values are lists of statistical methods ids;
        the statistical methods use result from the "key" basic quality method.

    consumers : dict
        a dictionary containing consumer processes to run, and their parameters

    feedback_obj : Feedback
        a Feedback container that contains information for the real-time feedback. Defaulted to None.

    Returns
    -------
    None
    """
    try:
        consumers = kwargs['consumers']
        consumer_zmq = init_consumers(consumers)
    except KeyError:
        consumer_zmq = None

    limits = args[0]
    quality_checks = args[1]
    aggregates = {}
    types = quality_checks.keys()
    for type in types:
        aggregates[type] = Aggregate(type, quality_checks[type], **kwargs)

    interrupted = False
    index = 0
    while not interrupted:
        try:
            data = dataq.get(timeout=0.005)
            if data.status == const.DATA_STATUS_END:
                interrupted = True
                send_to_consumers(consumer_zmq, data, const.DATA_STATUS_END)
                try:
                    feedbackq = kwargs['feedbackq']
                    for _ in range(len(aggregates)):
                        feedbackq.put(const.DATA_STATUS_END)
                except KeyError:
                    pass

            elif data.status == const.DATA_STATUS_MISSING:
                index += 1

            elif data.status == const.DATA_STATUS_DATA:
                type = data.type
                results = calc.run_quality_checks(data, index, aggregates[type], limits[type], quality_checks[type])
                send_to_consumers(consumer_zmq, data, results)
                try:
                    results.file_name = data.file_name
                except:
                    pass
                aggregates[results.type].handle_results(results)
                index += 1

        except queue.Empty:
            pass

    if reportq is not None:
        results = {}
        for type in aggregates:
            if not aggregates[type].is_empty():
                results[type] = {'bad_indexes': aggregates[type].bad_indexes, 'good_indexes': aggregates[type].good_indexes,
                           'results': aggregates[type].results}
        reportq.put(results)


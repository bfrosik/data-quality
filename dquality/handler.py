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

from multiprocessing import Queue, Process
import dquality.common.constants as const
import dquality.common.qualitychecks as calc
from dquality.common.containers import Aggregate
import sys
if sys.version[0] == '2':
    import Queue as queue
else:
    import queue as queue

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['num_stat_processes_on_result',
           'handle_data']


def num_stat_processes_on_result(result, aggregate, resultsq, limits, quality_checks):
    """
    This function calls handle_result function on aggregate that returns true if all calculation results for this
    slice passed validation, and False if any of them did not.
    If the passed, a sequence of statistical validations determined by a function mapper is started, each check
    as a new process. This function returns a number of processes it has started.

    Parameters
    ----------
    result : Result object
        result object with information about result, and calculation

    aggregate : Aggregate object
        aggregate for the type of data that is assessing data integrity. If one of the data checks failed for the data,
        the data is considered as failed. This object aggregates the results.

    resultsq : Queue
        a queue that will be used to pass result to receiving process.

    limits : dict
        a collection of limits as read from configuration

    quality_checks : dict
        a dictionary by data type of quelity check dictionaries:
        keys are ids of the basic quality check methods, and values are lislts of statistical methods ids;
        the statistical methods use result from the "key" basic quality method.

    Returns
    -------
    int
        number of statistical processes started
    """
    ret = 0
    # start statistical processes only when all results for this frame passed quality checks, and if the
    # result is not a statistical process
    quality_checks = quality_checks[result.data_type]
    if aggregate.all_good_on_result(result) and result.quality_id < const.STAT_START:
        for function_id in quality_checks[result.quality_id]:
            function = calc.function_mapper[function_id]
            p = Process(target=function, args=(result, aggregate, resultsq, limits,))
            p.start()
            ret += 1
    return ret

def handle_data(dataq, limits, reportq, quality_checks, feedback_obj=None):
    """
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

    feedback_obj : Feedback
        a Feedback container that contains information for the real-time feedback. Defaulted to None.

    Returns
    -------
    None
    """
    feedbackq = None
    if feedback_obj is not None:
        feedbackq = Queue()

    aggregates = {}
    types = quality_checks.keys()
    for type in types:
        aggregates[type] = Aggregate(type, quality_checks[type], feedbackq, feedback_obj)

    resultsq = Queue()
    interrupted = False
    index = 0
    num_processes = 0
    while not interrupted:
        try:
            data = dataq.get(timeout=0.005)
            if data == 'all_data':
                interrupted = True
                while num_processes > 0:
                    result = resultsq.get()
                    num_processes += (num_stat_processes_on_result(result, aggregates[result.data_type], resultsq, limits, quality_checks) - 1)
                if feedbackq is not None:
                    for _ in range(len(aggregates)):
                        feedbackq.put('all_data')

            elif data == 'missing':
                index += 1

            else:
                for function_id in quality_checks[data.type].keys():
                    function = calc.function_mapper[function_id]
                    p = Process(target=function, args=(data, index, resultsq, limits,))
                    p.start()
                    num_processes += 1
                index += 1

        except queue.Empty:
            pass

        while not resultsq.empty():
            result = resultsq.get_nowait()
            num_processes += (num_stat_processes_on_result(result, aggregates[result.data_type], resultsq, limits, quality_checks) - 1)

    if reportq is not None:
        results = {}
        for type in aggregates:
            if not aggregates[type].is_empty():
                results[type] = {'bad_indexes': aggregates[type].bad_indexes, 'good_indexes': aggregates[type].good_indexes,
                           'results': aggregates[type].results}
        reportq.put(results)


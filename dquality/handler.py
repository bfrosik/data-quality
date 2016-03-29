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
from Queue import Empty
import dquality.common.qualitychecks as calc
import common.constants as const
from common.containers import Aggregate
from common.qualitychecks import validate_stat_mean

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['handle_result',
           'handle_data']

# This map maps a list of statistical quality checks that are dependent on previous calculation to a calculation type.
function_mapper = {const.QUALITYCHECK_MEAN : [validate_stat_mean], const.QUALITYCHECK_STD : []}

def handle_result(result, aggregate, statq, limits):
    """
    This function calls handle_result function on aggregate that returns true if all calculation results for this
    slice passed validation, and False if any of them did not.
    If the passed, a sequence of statistical validations determined by a function mapper is started, each check
    as a new process. This function returns a nimber of processes it has started.

    Parameters
    ----------
    result : Result object
        result object with information about result, and calculation

    aggregate : Aggregate object
        aggregate for the type of data that is assessing data integrity. If one of the data checks failed for the data,
        the data is considered as failed. This object aggregates the results.

    statq : Queue
        a queue that will be used by statistical process to pass result to receiving process.

    limits : dict
        a collection of limits as read from configuration

    Returns
    -------
    int
        number of statistical processes started
    """
    ret = 0
    if aggregate.handle_result(result):
        for function in function_mapper[result.quality_id]:
            p = Process(target=function, args=(result, aggregate, statq, limits,))
            p.start()
            ret += 1
    return ret

def handle_stat_result(result, aggregate):
    """
    This function calls handle_result function on aggregate.

    Parameters
    ----------
    result : Result object
        result object with information about result, and calculation

    aggregate : Aggregate object
        aggregate for the type of data that is assessing data integrity. If one of the data checks failed for the data,
        the data is considered as failed. This object aggregates the results.

    Returns
    -------
    None
    """
    aggregate.handle_result(result)

def handle_data(dataq, limits, data_type, reportq):
    """
    This function is typically called as a new process. It takes a dataq parameter
    that is the queue on which data is received. It takes the dictionary containing limit values,
    and a data_type indication whether the data to be processed is data_dark, data_white, or data.
    Lastly, it takes a reportq parameter, a queue, which is used to report results.

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
        a dictionary of limits keyed by the data type

    data_type : str
        a constant indicating which type of data is to be processed
        i.e. 'data_dark', 'data_white", 'data'

    reportq : Queue
       results queue; used to pass results to the calling process

    Returns
    -------
    None
    """
    aggregate = Aggregate()
    resultsq = Queue()
    statq = Queue()
    interrupted = False
    index = 0
    max_index = 0
    stat_index = 0
    while not interrupted:
        try:
            data = dataq.get(timeout=0.005)
            if data == 'all_data':
                interrupted = True
                while max_index < index + const.NUMBER_CHECKS-1 and stat_index > 0:
                    # result = resultsq.get(timeout=0.005)
                    # max_index = max(result.index,max_index)
                    # if handle_result(result, aggregate, statq, limits):
                    #     stat_index = stat_index + 1
                    # print (data_type, result.index-result.quality_id,result.quality_id,result.res,result.error)
                    # while not statq.empty():
                    #     result = statq.get_nowait()
                    #     stat_index = stat_index -1
                    #     handle_stat_result(result, aggregate)
                    #     print (data_type, result.index-result.quality_id,result.quality_id,result.res,result.error)

                    while not resultsq.empty():
                        result = resultsq.get()
                        max_index = max(result.index,max_index)
                        stat_index += handle_result(result, aggregate, statq, limits)
                        print (data_type, result.index-result.quality_id,result.quality_id,result.res,result.error)

                    while not statq.empty():
                        result = statq.get_nowait()
                        stat_index -= 1
                        handle_stat_result(result, aggregate)
                        print (data_type, result.index-result.quality_id,result.quality_id,result.res,result.error)
            else:
                slice = data.slice
                p1 = Process(target=calc.validate_mean_signal_intensity, args=(slice, index, resultsq, limits,))
                p2 = Process(target=calc.validate_signal_intensity_standard_deviation, args=(slice, index, resultsq, limits,))
                p2.start()
                p1.start()
                index += 1
        except Empty:
            pass

        while not resultsq.empty():
            result = resultsq.get_nowait()
            max_index = max(result.index,max_index)
            if handle_result(result, aggregate, statq, limits):
                stat_index += 1
            print (data_type, result.index-result.quality_id,result.quality_id,result.res,result.error)

        while not statq.empty():
            result = statq.get_nowait()
            stat_index -= 1
            handle_stat_result(result, aggregate)
            print (data_type, result.index-result.quality_id,result.quality_id,result.res,result.error)

    results = {}
    results['bad_indexes'] = aggregate.bad_indexes
    results['good_indexes'] = aggregate.good_indexes
    results['results'] = aggregate.results
    reportq.put(results)
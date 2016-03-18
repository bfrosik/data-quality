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

This module verifies a given file according to schema configuration and
starts new processes, each process performing specific quality calculations.

The results will be reported in a file (printed on screen for now)

"""

from multiprocessing import Queue, Process
from Queue import Empty
import dquality.common.qualitychecks as calc
import common.constants as const

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['handle_result',
           'handle_data']

class Data:
    def __init__(self, slice, theta):
        self.slice = slice
        self.theta = theta

class Aggregate:
    mean_values = []
    stds = []
    results = {const.QUALITYCHECK_MEAN : mean_values, const.QUALITYCHECK_STD: stds}
    theta = []
    last_theta = 0
    bad_index = []

def handle_result(result):
    pass

def handle_data(dataq, all_limits, data_type):
    """
    This function is typically called as a new process. It takes a dataq parameter
    that is the queue on which data is received. It takes the dictionary containing limit values,
    and a data_type indication whether the data to be processed is data_dark, data_white, or data.

    The initialization constrains of retrieving limits corresponding to the data type, creating
    queue for results passing, and initializing variables.

    This function has a loop that retrieves data from the data queue, runs a sequence of
    validation methods on the data, and retrieves results from rhe results queue.
    Each result object contains information whether the data was out of limits, in addition
    to the value and index. Each result is additionally evaluated with relation to the prvious
    accumulated results.

    The loop is interrupted when the data queue received end of data element in the queue, and all
    processes produced results.


    Parameters
    ----------
    dataq : Queue
        data queuel; data is received in this queue

    all_limits : dictionary
        a dictionary of limits keyed by the data type

    data_type : str
        a constant indicating which type of data is to be processed
        can be 'data_dark', 'data_white", 'data'

    Returns
    -------
    None
    """
    resultsq = Queue()
    limits = all_limits[data_type]
    interrupted = False
    index = 0
    max_index = 0
    while not interrupted:
        try:
            data = dataq.get(timeout=0.005)
            if data == 'all_data':
                interrupted = True
                while max_index < index + const.NUMBER_CHECKS-1:
                    result = resultsq.get()
                    max_index = max(result.index,max_index)
                    handle_result(result)
                    print (result.index,result.quality_id,result.error)

            else:
                slice = data.slice
                p1 = Process(target=calc.validate_mean_signal_intensity, args=(slice, index,resultsq, limits,))
                p2 = Process(target=calc.validate_signal_intensity_standard_deviation, args=(slice, index,resultsq, limits,))
                p2.start()
                p1.start()
                index = index + 1
        except Empty:
            pass

        while not resultsq.empty():
            result = resultsq.get_nowait()
            max_index = max(result.index,max_index)
            handle_result(result)
            print (result.index,result.quality_id,result.error)

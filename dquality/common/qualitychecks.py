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
This file is a suite of verification functions for scientific data.

"""

import numpy as np
import dquality.common.constants as const
from dquality.common.containers import Result, Results

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['find_result',
           'validate_mean_signal_intensity',
           'validate_signal_intensity_standard_deviation',
           'validate_stat_mean']


def find_result(res, quality_id, limits):
    """
    This creates and returns Result instance determined by the given parameters.

    It evaluates given result value against limits, and creates Result instance.

    Parameters
    ----------
    res : float
        calculated result

    quality_id : int
        id of the quality check function

    limits : dictionary
        a dictionary containing threshold values

    Returns
    -------
    result : Result
        a Result object

    """
    if res < limits['low_limit']:
        result = Result(res, quality_id, const.QUALITYERROR_LOW)
    elif res > limits['high_limit']:
        result = Result(res, quality_id, const.QUALITYERROR_HIGH)
    else:
        result = Result(res, quality_id, const.NO_ERROR)
    return result


def validate_mean_signal_intensity(data, limits):
    """
    This method validates mean value of the frame.

    This function calculates mean signal intensity of the data slice. The result is compared with threshhold
    values to determine the quality of the data. The result, comparison result, index, and quality_id values are
    saved in a new Result object.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data

    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    Returns
    -------
    result : Result
        a Result object
    """

    this_limits = limits['mean']
    res = np.mean(data.slice)
    result = find_result(res, const.QUALITYCHECK_MEAN, this_limits)
    return result


def validate_signal_intensity_standard_deviation(data, limits):
    """
    This method validates standard deviation value of the frame.

    This function calculates standard deviation of the data slice. The result is compared with threshhold
    values to determine the quality of the data. The result, comparison result, index, and quality_id values are
    saved in a new Result object.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data

    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    Returns
    -------
    result : Result
        a Result object
    """

    this_limits = limits['std']
    res = np.std(data.slice)
    result = find_result(res, const.QUALITYCHECK_STD, this_limits)
    return result


def validate_intensity_sum(data, limits):
    """
    This method validates a sum of all intensities value of the frame.

    This function calculates sums the pixels intensity in the given frame. The result is compared with
    threshhold values to determine the quality of the data. The result, comparison result, index, and quality_id values
    are saved in a new Result object.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data

    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    Returns
    -------
    result : Result
        a Result object
    """
    this_limits = limits['sum']
    res = data.slice.sum()
    result = find_result(res, const.QUALITYCHECK_SUM, this_limits)
    return result


def validate_cnt_rate_sat(data, limits):
    """
    This method validates a sum of all intensities value of the frame.

    This function calculates sums the pixels intensity in the given frame. The result is compared with
    threshhold values to determine the quality of the data. The result, comparison result, index, and quality_id values
    are saved in a new Result object.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data

    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    Returns
    -------
    result : Result
        a Result object
    """
    this_limits = limits['rate_sat']
    acq_time = data.acq_time
    res = data.slice.sum()/acq_time
    result = find_result(res, const.QUALITYCHECK_RATE_SAT, this_limits)
    return result


def validate_frame_saturation(data, limits):
    """
    This method validates saturation value of the frame.

    This function calculates calculates the number of saturated pixels in the given frame. The result is compared with
    threshhold values to determine the quality of the data. The result, comparison result, index, and quality_id values
    are saved in a new Result object.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data

    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    Returns
    -------
    result : Result
        a Result object
    """
    this_limits = limits['frame_sat']
    sat_high = (limits['sat'])['high_limit']
    res = (data.slice > sat_high).sum()
    result = Result(res, const.QUALITYCHECK_FRAME_SAT, this_limits)
    return result


def validate_saturation(data, limits):
    """
    This method validates saturation value of the frame.

    This function calculates calculates the number of saturated pixels in the given frame. The result is compared with
    threshhold values to determine the quality of the data. The result, comparison result, index, and quality_id values
    are saved in a new Result object.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data

    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    Returns
    -------
    result : Result
        a Result object
    """
    sat_high = (limits['sat'])['high_limit']
    res = (data.slice > sat_high).sum()
    result = Result(res, const.QUALITYCHECK_SAT, const.NO_ERROR)
    return result


def validate_stat_mean(limits, aggregate, results):
    """
    This is one of the statistical validation methods.

    It has a "quality_id"
    This function evaluates current mean signal intensity with relation to statistical data captured
    in the aggregate object. The delta is compared with threshhold values.
    The result, comparison result, index, and quality_id values are saved in a new Result object.

    Parameters
    ----------
    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    aggregate : Aggregate
        aggregate instance containing calculated results of previous slices

    results : dict
        a dictionary containing all results of quality checks for the evaluated frame, keyed by quality check ID

    Returns
    -------
    result : Result
        a Result object
    """
    this_limits = limits['stat_mean']

    stat_data = aggregate.get_results(const.QUALITYCHECK_MEAN)
    length = len(stat_data)
    # calculate std od mean values in aggregate
    if length == 0:
        return find_result(0, const.STAT_MEAN, this_limits)
    elif length == 1:
        mean_mean = np.mean(stat_data)
    else:
        mean_mean = np.mean(stat_data[0:(length -1)])

    result = results[const.QUALITYCHECK_MEAN]
    delta = result.res - mean_mean

    result = find_result(delta, const.STAT_MEAN, this_limits)
    return result


def validate_accumulated_saturation(limits, aggregate, results):
    """
    This is one of the statistical validation methods.

    It has a "quality_id"
    This function adds ecurrent saturated pixels number to the total kept in the aggregate object.
    The total is compared with threshhold values. The result, comparison result, index, and quality_id values are
    saved in a new Result object.

    Parameters
    ----------
    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    aggregate : Aggregate
        aggregate instance containing calculated results of previous slices

    results : dict
        a dictionary containing all results of quality checks for the evaluated frame, keyed by quality check ID

    Returns
    -------
    result : Result
        a Result object
    """
    this_limits = limits['sat_points']
    stat_data = aggregate.get_results(const.QUALITYCHECK_SAT)
    # calculate total saturated points
    result = results[const.QUALITYCHECK_SAT]
    total = np.sum(stat_data) + result.res

    result = find_result(total, const.ACC_SAT, this_limits)
    return result


# maps the quality check ID to the function object
function_mapper = {const.QUALITYCHECK_MEAN : validate_mean_signal_intensity,
                   const.QUALITYCHECK_STD : validate_signal_intensity_standard_deviation,
                   const.QUALITYCHECK_SAT : validate_saturation,
                   const.QUALITYCHECK_FRAME_SAT : validate_frame_saturation,
                   const.QUALITYCHECK_RATE_SAT: validate_cnt_rate_sat,
                   const.QUALITYCHECK_SUM: validate_intensity_sum,
                   const.STAT_MEAN : validate_stat_mean,
                   const.ACC_SAT : validate_accumulated_saturation}

def run_quality_checks(data, index, resultsq, aggregate, limits, quality_checks):
    """
    This function runs validation methods applicable to the frame data type and enqueues results.

    This function calls all the quality checks and creates Results object that holds results of each quality check, and
    attributes, such data type, index, and status. This object is then enqueued into the "resultsq" queue.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data

    index : int
        frame index

    resultsq : Queue
         a queue to which the results are enqueued

    aggregate : Aggregate
        aggregate instance containing calculated results of previous slices

    limits : dictionary
        a dictionary containing threshold values for the evaluated data type

    quality_checks : list
        a list of quality checks that apply to the data type

    Returns
    -------
    none
    """
    quality_checks.sort()
    results_dir = {}
    failed = False
    for function_id in quality_checks:
        function = function_mapper[function_id]
        if function_id < const.STAT_START:
            result = function(data, limits)
            results_dir[function_id] = result
            if result.error != 0:
                failed = True
        else:
            if not failed:
                result = function(limits, aggregate, results_dir)
                results_dir[function_id] = result
                if result.error != 0:
                    failed = True

    results = Results(data.type, index, failed, results_dir)
    resultsq.put(results)

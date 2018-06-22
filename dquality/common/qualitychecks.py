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
           'mean',
           'st_dev',
           'sum',
           'frame_sat_cnt_rate',
           'frame_sat_pts',
           'stat_mean',
           'acc_sat',
           'run_quality_checks']


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
    try:
        ll = limits['low_limit']
        if res < ll:
            return Result(res, quality_id, const.QUALITYERROR_LOW)
    except KeyError:
        pass

    try:
        hl = limits['high_limit']
        if res > hl:
            return Result(res, quality_id, const.QUALITYERROR_HIGH)
    except KeyError:
        pass

    return Result(res, quality_id, const.NO_ERROR)


def mean(**kws):
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
    limits = kws['limits']
    data = kws['data']

    this_limits = limits['mean']
    res = np.mean(data.slice)
    result = find_result(res, 'mean', this_limits)
    return result


def st_dev(**kws):
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
    limits = kws['limits']
    data = kws['data']

    this_limits = limits['std']
    res = np.std(data.slice)
    result = find_result(res, 'st_dev', this_limits)
    return result


def sum(**kws):
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
    limits = kws['limits']
    data = kws['data']

    this_limits = limits['sum']
    res = data.slice.sum()
    result = find_result(res, 'sum', this_limits)

    return result


def frame_sat_cnt_rate(**kws):
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
    # limits = kws['limits']
    # data = kws['data']
    #
    # this_limits = limits['rate_sat']
    # acq_time = data.rate_sat
    # res = data.slice.sum()/acq_time
    # result = find_result(res, 'rate_sat', this_limits)
    # return result
    #
    limits = kws['limits']
    data = kws['data']

    # find how many pixels have saturation rate (intensity divided by acquire time) exceeding the
    # point saturation rate limit
    acq_time = data.acq_time
    sat_high = (limits['point_sat_rate'])['high_limit']
    points = (data.slice/acq_time > sat_high).sum()

    # evaluate if the number of saturated points are within limit
    this_limits = limits['frame_sat_cnt_rate']
    result = find_result(points, 'frame_sat_cnt_rate', this_limits)
    return result


def frame_sat_pts(**kws):
    """
    This method validates saturation value of the frame.

    This function calculates the number of saturated pixels in the given frame. The result is compared with
    threshold value to determine the quality of the data. The result, comparison result, index, and quality_id values
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
    limits = kws['limits']
    data = kws['data']

    # find how many pixels have intensity exceeding the point saturation limit
    sat_high = (limits['point_sat'])['high_limit']
    points = (data.slice > sat_high).sum()

    # evaluate if the number of saturated points are within limit
    this_limits = limits['frame_sat_pts']
    result = find_result(points, 'frame_sat_pts', this_limits)
    return result


def stat_mean(**kws):
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
    limits = kws['limits']
    aggregate = kws['aggregate']
    results = kws['results']

    this_limits = limits['stat_mean']

    stat_data = aggregate.get_results('mean')
    length = len(stat_data)
    # calculate std od mean values in aggregate
    if length == 0:
        return find_result(0, 'stat_mean', this_limits)
    elif length == 1:
        mean_mean = np.mean(stat_data)
    else:
        mean_mean = np.mean(stat_data[0:(length -1)])

    result = results['mean']
    delta = result.res - mean_mean

    result = find_result(delta, 'stat_mean', this_limits)
    return result


def acc_sat(**kws):
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
    limits = kws['limits']
    aggregate = kws['aggregate']
    results = kws['results']

    this_limits = limits['sat_points']
    stat_data = aggregate.get_results('frame_sat')
    # calculate total saturated points
    result = results['saturation']
    total = np.sum(stat_data) + result.res

    result = find_result(total, 'acc_sat', this_limits)
    return result


# maps the quality check ID to the function object
function_mapper = {'mean' : mean,
                   'st_dev' : st_dev,
                   'frame_sat_pts' : frame_sat_pts,
                   'frame_sat_cnt_rate': frame_sat_cnt_rate,
                   'sum': sum,
                   'stat_mean' : stat_mean,
                   'acc_sat' : acc_sat}

def run_quality_checks(data, index, aggregate, limits, quality_checks):
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
    #quality_checks.sort()
    results_dict = {}
    failed = False
    for qc in quality_checks:
        function = function_mapper[qc]
        result = function(limits=limits, data=data, aggregate=aggregate, results=results_dict)

        results_dict[qc] = result
        if result.error != 0:
            failed = True

    results = Results(data.type, index, failed, results_dict)
    return results

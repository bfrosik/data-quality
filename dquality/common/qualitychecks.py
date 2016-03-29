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
import constants as const
from containers import Result

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['validate_mean_signal_intensity',
           'validate_signal_intensity_standard_deviation',
           'validate_voxel_based_SNR'
           'validate_slice_based_SNR']



def validate_mean_signal_intensity(data, index, results, all_limits):
    """
    Currently a stub function.
    This is one of the validation methods. It has a "quality_id"
    property that identifies this validation step. This function
    calculates mean signal intensity from the data parameter. The
    result is compared with threshhold values to determine the
    quality of the data. The "file" parameter, result, the
    comparison result, "process_id" parameter, and quality_id
    values are saved in a new Result object. This object is then
    enqueued into the "results" queue.

    Parameters
    ----------
    data : Data
        data instance that includes File Name and data

    process_id : int
        Unique process id assigned by a calling function

    results : Queue
        A multiprocessing.Queue instance that is used to pass the
        results from validating processes to the main

    Returns
    -------
    None
    """
    limits = all_limits['mean']
    res = np.mean(data)
    quality_id = const.QUALITYCHECK_MEAN
    if res < limits['low_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_LOW)
    elif res > limits['high_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_HIGH)
    else:
        result = Result(res, index+quality_id, quality_id, const.NO_ERROR)
    results.put(result)

def validate_signal_intensity_standard_deviation(data, index, results, all_limits):
    """
    Currently a stub function.
    This is one of the validation methods. It has a "quality_id"
    property that identifies this validation step. This function
    calculates signal intensity standard deviation from the data
    parameter. The result is compared with threshhold values to
    determine the quality of the data. The "file" parameter, result,
    the comparison result, "process_id" parameter, and quality_id
    values are saved in a new Result object. This object is then
    enqueued into the "results" queue.

    Parameters
    ----------
    data : Data
        data instance that includes File Name and data

    process_id : int
        Unique process id assigned by a calling function

    results : Queue
        A multiprocessing.Queue instance that is used to pass
        the results from validating processes to the main

    Returns
    -------
    None
    """
    limits = all_limits['std']
    res = np.std(data)
    quality_id = const.QUALITYCHECK_STD
    if res < limits['low_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_LOW)
    elif res > limits['high_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_HIGH)
    else:
        result = Result(res, index+quality_id, quality_id, const.NO_ERROR)
    results.put(result)

def validate_stat_mean(result, aggregate, results, all_limits):
    """
    Currently a stub function.
    This is one of the validation methods. It has a "quality_id"
    property that identifies this validation step. This function
    calculates signal intensity standard deviation from the data
    parameter. The result is compared with threshhold values to
    determine the quality of the data. The "file" parameter, result,
    the comparison result, "process_id" parameter, and quality_id
    values are saved in a new Result object. This object is then
    enqueued into the "results" queue.

    Parameters
    ----------
    data : Data
        data instance that includes File Name and data

    process_id : int
        Unique process id assigned by a calling function

    results : Queue
        A multiprocessing.Queue instance that is used to pass
        the results from validating processes to the main

    Returns
    -------
    None
    """
    limits = all_limits['stat_mean']
    quality_id = const.STAT_MEAN
    length = aggregate.get_results_len(const.QUALITYCHECK_MEAN)
    stat_data = aggregate.results[const.QUALITYCHECK_MEAN]
    # calculate std od mean values in aggregate
    if length == 1:
        mean_mean = np.mean(stat_data)
    else:
        mean_mean = np.mean(stat_data[0:(length -1)])
    delta = result.res - mean_mean
    index = result.index - result.quality_id

    if delta < limits['low_limit']:
        result = Result(delta, index+quality_id, quality_id, const.QUALITYERROR_LOW)
    elif delta > limits['high_limit']:
        result = Result(delta, index+quality_id, quality_id, const.QUALITYERROR_HIGH)
    else:
        result = Result(delta, index+quality_id, quality_id, const.NO_ERROR)
    results.put(result)

def validate_slice_based_SNR(data, index, results, all_limits):
    """
    Currently a stub function.
    This is one of the validation methods. It has a "quality_id"
    property that identifies this validation step. This function
    calculates voxel-based signal to noise ratio from the data
    parameter. The result is compared with threshhold values to
    determine the quality of the data. The "file" parameter, result,
    the comparison result, "process_id" parameter, and quality_id
    values are saved in a new Result object. This object is then
    enqueued into the "results" queue.

    Parameters
    ----------
    data : Data
        data instance that includes File Name and data

    process_id : int
        Unique process id assigned by a calling function

    results : Queue
        A multiprocessing.Queue instance that is used to pass the
        results from validating processes to the main

    Returns
    -------
    None
    """
    limits = all_limits['std']
    res = np.std(data)
    quality_id = const.QUALITYCHECK_STD
    if res < limits['low_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_LOW)
    elif res > limits['high_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_HIGH)
    else:
        result = Result(res, index+quality_id, quality_id, const.NO_ERROR)
    results.put(result)

def validate_voxel_based_SNR(data, index, results, all_limits):
    """
    Currently a stub function.
    This is one of the validation methods. It has a "quality_id"
    property that identifies this validation step. This function
    calculates voxel-based signal to noise ratio from the data
    parameter. The result is compared with threshhold values to
    determine the quality of the data. The "file" parameter, result,
    the comparison result, "process_id" parameter, and quality_id
    values are saved in a new Result object. This object is then
    enqueued into the "results" queue.

    Parameters
    ----------
    data : Data
        data instance that includes File Name and data

    process_id : int
        Unique process id assigned by a calling function

    results : Queue
        A multiprocessing.Queue instance that is used to pass the
        results from validating processes to the main

    Returns
    -------
    None
    """
    limits = all_limits['std']
    res = np.std(data)
    quality_id = const.QUALITYCHECK_STD
    if res < limits['low_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_LOW)
    elif res > limits['high_limit']:
        result = Result(res, index+quality_id, quality_id, const.QUALITYERROR_HIGH)
    else:
        result = Result(res, index+quality_id, quality_id, const.NO_ERROR)
    results.put(result)


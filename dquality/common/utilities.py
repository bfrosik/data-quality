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
This file is a suite of utility functions.

"""

import h5py
import logging

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['lt',
           'le',
           'eq',
           'ge',
           'gt',
           'get_data',
           'copy_list',
           'key_list',
           'report_items']

logger = logging.getLogger(__name__)


def lt(value, limit):
    """
    This function returns True if value parameter is less than limit
    parameter, False otherwise.

    Parameters
    ----------
    value : numeric
        value

    limit : numeric
        limit

    Returns
    -------
    boolean
    """
    return value < limit


def le(value, limit):
    """
    This function returns True if value parameter is less than or
    equal to limit parameter, False otherwise.

    Parameters
    ----------
    value : numeric
        value

    limit : numeric
        limit

    Returns
    -------
    boolean
    """
    return value <= limit


def eq(value, limit):
    """
    This function returns True if value parameter is equal to
    limit parameter, False otherwise.

    Parameters
    ----------
    value : numeric
        value

    limit : numeric
        limit

    Returns
    -------
    boolean
    """
    return value == limit


def ge(value, limit):
    """
    This function returns True if value parameter is greater
    than or equal to limit parameter, False otherwise.

    Parameters
    ----------
    value : numeric
        value

    limit : numeric
        limit

    Returns
    -------
    boolean
    """
    return value >= limit


def gt(value, limit):
    """
    This function returns True if value parameter is greater than
    limit parameter, False otherwise.

    Parameters
    ----------
    value : numeric
        value

    limit : numeric
        limit

    Returns
    -------
    boolean
    """
    return value > limit


def get_data(file):
    """
   This function takes a file of HD5 format, traverses through tags,
   finds "shape" data sets and returns the sets in a dictionary.

    Parameters
    ----------
    file : str
        File Name

    Returns
    -------
    data : dictionary
        A dictionary of data sets with the tag keys
    """
    data = {}

    def func(name, dset):
        if not hasattr(dset, 'shape'):
            return  # not array, can't be image
        if isinstance(dset, h5py.Dataset):
            data[dset.name] = dset

    file_h5 = h5py.File(file, 'r')
    file_h5.visititems(func)
    return data


def copy_list(list):
    """
   This function takes a list and returns a hardcopy.

    Parameters
    ----------
    list : list
        A list

    Returns
    -------
    lisle : list
        A hard copy of list parametyer
    """
    listcopy = []
    for item in list:
        listcopy.append(item)
    return listcopy


def key_list(dict):
    """
   This function takes a dictionary and returns a new list of keys.

    Parameters
    ----------
    dict : dictionary
        A dictionary

    Returns
    -------
    lisle : list
        A new list of keys in dictionary
    """
    list = []
    for key in dict:
        list.append(key)
    return list


def report_items(list, text1, text2):
    """
   This function takes a list and strings. If the list is not
   empty it prints the two string parameters as a title,
   and prints formatted output for each item in a list.

    Parameters
    ----------
    list : list
        A list of items

    text1 : str
        A title that will be printed if the list is not empty

    text2 : str
        An optional part of title that will be printed if
        the list is not empty

    Returns
    -------
    None
    """
    if len(list) > 0:
        logger.info(text1 + text2)
        for item in list:
            logger.info('    - ' + item)

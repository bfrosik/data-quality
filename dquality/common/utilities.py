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
import os
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
           'get_logger',
           'get_directory',
           'get_file',
           'get_data_hd5',
           'copy_list',
           'key_list']



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


def get_logger(name, conf):
    """
    This function initializes logger. If logger is not configured or the logging directory does not exist,
    the logging messages will be added into default.log file.

    Parameters
    ----------
    name : str
        name of the logger, typically name of file that uses the logger

    conf : config Object
        a configuration object

    Returns
    -------
    logger : logger
    """
    logger = logging.getLogger(name)
    try:
        log_file_name = conf['log_file']
        logging.basicConfig(filename=log_file_name, level=logging.DEBUG)
    except KeyError:
        print('config error: log file is not configured, logging to default.log')
        logging.basicConfig(filename='default.log', level=logging.DEBUG)
    except:
        print('config error: log file directory does not exist')
        logging.basicConfig(filename='default.log', level=logging.DEBUG)
    return logger

def get_directory(conf, logger):
    """
    This function returns a directory object. It reads the directory from a configuration file.
    If the directory is not configured or does not exist a message is logged into a log file,
    and None is returned.

    Parameters
    ----------
    conf : config Object
        a configuration object

    logger : Logger Object
        a logger object

    Returns
    -------
    folder : str
    """
    try:
        # check if directory exists
        folder = conf['directory']
        if not os.path.isdir(folder):
            logger.error(
                'configuration error: directory ' +
                folder + ' does not exist')
            return None
    except KeyError:
        logger.error('config error: directory to monitor not configured')
        return None
    return folder


def get_file(dir, conf, config_name, logger):
    """
    This function returns a file object. It reads the file from a configuration file.
    If the file is not configured or does not exist a message is logged into a log file,
    and None is returned.

    Parameters
    ----------
    dir : str
        a path the file starts with
        
    conf : config Object
        a configuration object

    config_name : str
        a key string defining the file in a configuration
        
    logger : Logger Object
        a logger object

    Returns
    -------
    folder : str
    """
    try:
        filename = conf[config_name]
        file = os.path.join(dir, filename)
        if not os.path.isfile(file):
            logger.error(
                'configuration error: file ' +
                file + ' does not exist')
            return None
    except KeyError:
        logger.error(
            'configuration error: ' +
            config_name + ' is not configured')
        return None
    return file


def get_data_hd5(file):
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
            data[dset.name] = dset.name

    file_h5 = h5py.File(file, 'r')
    file_h5.visititems(func)
    return file_h5, data


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



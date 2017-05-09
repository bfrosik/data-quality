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
import struct as st
import logging
from configobj import ConfigObj
import pytz
import datetime
import dquality.common.constants as const


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['lt',
           'le',
           'eq',
           'ge',
           'gt',
           'get_config',
           'get_logger',
           'get_directory',
           'get_file',
           'get_data_hdf',
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

def get_config(config):
    """
    This function returns configuration dictionary. It checks the conf_path parameter wheter it is directory
    or a file. If a directory, it appends 'dqconfig_test.ini' as a file name. If the directory or file does not
    exist, a message is printed on a console and None is returned. Otherwise, the file is processed into
    dictionary, that is returned.

    Parameters
    ----------
    config : str
        name of the configuration file including path, or path

    Returns
    -------
    conf : config Object
        a configuration object
    """
    if os.path.isdir(config):
        config = os.path.join(config, 'dqconfig.ini')
    if not os.path.isfile(config):
        return None

    return ConfigObj(config)


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

    timezone : str
        a standard string defining local timezone, for convenience initialized to known location

    Returns
    -------
    logger : logger
    """

    try:
        # try absolute path
        lfile = conf['log_file']
    except KeyError:
        print('config warning: log file is not configured, logging to default.log')
        lfile = 'default.log'
    except:
        print('config error: log file directory does not exist')
        lfile = 'default.log'

    try:
        timezone = conf['time_zone']
    except KeyError:
        timezone = 'America/Chicago'

    tz = pytz.timezone(timezone)

    class Formatter(logging.Formatter):
        def converter(self, timestamp):
            return datetime.datetime.fromtimestamp(timestamp, tz)

        def formatTime(self, record, datefmt=None):
            dt = self.converter(record.created)
            if datefmt:
                s = dt.strftime(datefmt)
            else:
                t = dt.strftime(self.default_time_format)
                s = self.default_msec_format % (t, record.msecs)
            return s

    logger = logging.getLogger(name)
    handler = logging.FileHandler(lfile)
    handler.setFormatter(Formatter("%(asctime)s:  %(levelname)s:  %(name)s:  %(message)s", "%Y-%m-%dT%H:%M:%S%z"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def get_file(conf, config_name, logger, log_error=True):
    """
    This function returns a file object. It reads the file from a configuration file.
    If the file is not configured or does not exist a message is logged into a log file,
    and None is returned.

    Parameters
    ----------
    conf : config Object
        a configuration object

    config_name : str
        a key string defining the file in a configuration
        
    logger : Logger Object
        a logger object

    Returns
    -------
    file : str
    """
    try:
        file = conf[config_name]
        if not os.path.isfile(file):
            logger.error(
                'configuration error: file ' +
                file + ' does not exist')
            return None
    except KeyError:
        if log_error:
            logger.error(
                'configuration error: ' +
                config_name + ' is not configured')
        return None
    return file


def get_data_hdf(file):
    """
    This function takes a file of HDF format, traverses through tags,
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


def get_data_ge(logger, file):
    """
    This function takes a file of GE format.

    Parameters
    ----------
    file : str
        File Name

    Returns
    -------
    data : dictionary
        A dictionary of data sets with the tag keys
    """
    fp = open(file, 'rb')
    offset = 8192

    fp.seek(18)
    size, nframes = st.unpack('<ih',fp.read(6))
    if size != 2048:
        logger.error('GE image size unexpected: '+str(size))
        return None, 0, 0

    fsize = os.stat(str(fp).split("'")[1]).st_size
    nframes_calc = (fsize - offset)/(2*size**2)

    if nframes != nframes_calc:
        logger.error('GE number frames unexpected: '+str(nframes))
        return None, 0, 0

    pos = offset
    fp.seek(pos)

    return fp, int(nframes_calc), size*size


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
    list : list
        A new list of keys in dictionary
    """
    list = []
    for key in dict:
        list.append(key)
    return list


def get_quality_checks(dict):
    """
    This function translates the strings into defined numerical values.

    This function takes a dictionary with all elements as strings, that are defined as constants in the
    dquality/common.constants.py file and replaces the strings with defined numerical values.

    Parameters
    ----------
    dict : dictionary
        A dictionary with string elements

    Returns
    -------
    quality_checks : dict
        A new dictionary with all elements replaced by the numerical values the strings represented
    """

    quality_checks = {}
    for type in dict:
        list = []
        for qc in dict[type]:
            list.append(const.get_id(qc))
        quality_checks[type] = list

    return quality_checks


def get_feedback_pvs(quality_checks):
    """
    This function translates numerical values into strings.

    This function takes a dictionary with numerical velues, representing the quality checks that apply to the data type
    (key). The numerical values are translated here to the string representations in a new dictionary.

    Parameters
    ----------
    quality_checks : dictionary
        a dictionary with numerical elements

    Returns
    -------
    feedback_pvs : dict
        A new dictionary with all elements replaced by the actual value the strings represented
    """
    feedback_pvs = []
    for type in quality_checks:
        qcs = quality_checks[type]
        for qc in qcs:
            qc_str = type + '_' + const.to_string(qc)
            feedback_pvs.append(qc_str)
    return feedback_pvs

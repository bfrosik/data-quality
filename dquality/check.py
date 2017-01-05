#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2015, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2015. UChicago Argonne, LLC. This software was produced       #
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
This module contains command line interface to data-quality. 
To use Please make sure the installation :ref:`pre-requisite-reference-label` are met.

"""

import json
import dquality.hdf as dqhdf
import dquality.data as dqdata
import dquality.hdf_dependency as dqdependency
import dquality.accumulator as acc
import dquality.monitor as dqdmonitor
import dquality.monitor_polling as dqpolmonitor
import dquality.pv as dqpv

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['hdf',
           'pv',
           'monitor',
           'accumulator',
           'data',
           'hdf_dependency']

def hdf(conf, fname):
    """
    HDF file structure verifier.

    Parameters
    ----------
    conf : str
        configuration file name, including path

    file : str
        File Name to verify including path

    Returns
    -------
    boolean


    """
    
    if dqhdf.verify(conf, fname):
        print ('All tags exist and meet conditions')
    else:
        print ('Some of the tags do not exist or do not meet conditions, check log file')

def pv(conf):
    """

    PV verifier.

    Parameters
    ----------
    conf : str
        configuration file name, including path

    Returns
    -------
    boolean

    """
    if dqpv.verify(conf):
        print ('All PVs listed in pvs.json exist and meet conditions')
    else:
        print ('Some of the PVs listed in pvs.json do not exist or do not meet conditions')


def monitor(conf, folder, num_files):
    """
    Data quality monitor verifier.
    
    Parameters
    ----------
    conf : str
        configuration file name including path

    folder : str
        folder name to monitor

    num_files : int
        expected number of files. This script will exit after detecting and
        processing given number of files.

    Returns
    -------
    None

    """

    bad_indexes = dqdmonitor.verify(conf, folder, int(num_files))
    return bad_indexes


def monitor_polling(conf, folder, num_files):
    """
    Data quality monitor verifier.

    Parameters
    ----------
    conf : str
        configuration file name including path

    folder : str
        folder name to monitor

    num_files : int
        expected number of files. This script will exit after detecting and
        processing given number of files.

    Returns
    -------
    None

    """
    bad_indexes = dqpolmonitor.verify(conf, folder, int(num_files))
    return bad_indexes


def accumulator(conf, fname, dtype, num_files, report_by_file):
    """
    Data Quality monitor.
    
    Parameters
    ----------
    conf : str
        configuration file name, including path

    folder : str
        monitored directory

    data_type : str
        defines which data type is being evaluated

    num_files : int
        number of files that will be processed

    report_by_files : boolean
        this variable directs how to present the bad indexes in a report. If True, the indexes
        are related to the files, and a filename is included in the report. Otherwise, the
        report contains a list of bad indexes.

    Returns
    -------
    bad_indexes : dict
        a dictionary or list containing bad indexes
    """
    
    bad_indexes = acc.verify(conf, fname, dtype, int(num_files), report_by_file)
    print (json.dumps(bad_indexes))
    return bad_indexes


def data(conf, fname):
    """
    Data Quality verifier.
    
    Parameters
    ----------
    conf : str
        name of the configuration file including path. If contains only directory, 'dqconfig_test.ini' will a default
        file name.

    file : str
        file name to do the quality checks on

    Returns
    -------
    bad_indexes : Dict
    """

    bad_indexes = dqdata.verify(conf, fname)
    print (json.dumps(bad_indexes))
    return bad_indexes


def hdf_dependency(conf, fname):
    """
    Dependency verifier.

    Parameters
    ----------
    conf : str
        configuration file name, including path

    file : str
        File Name to verify including path

    Returns
    -------
    boolean
    
    """

    if dqdependency.verify(conf, fname):
        print ('All dependecies are satisfied')
    else:
        print ('Some dependecies are not satisfied, see log file')




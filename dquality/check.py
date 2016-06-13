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
This module contains command line interface to data-quality

"""

import sys
import json
import argparse
import dquality.file as hdf
import dquality.data as data
import dquality.monitor as monitor
import dquality.data_monitor as dmonitor
import dquality.pv as pv

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['hdf_check',
           'pv_check',
           'monitor_quality_check',
           'monitor_check',
           'dquality_check',
           'dependency_check']


def hdf_check(arg):
    """
    Please make sure the installation :ref:`pre-requisite-reference-label` are met.

    This example shows how to verify an HDF file structure.
    This example takes two mandatory command line arguments:
    conf: a string defining the configuration file. If only path is defined, the name 'dqconfig_test.ini'
    file: a file to be verified.

    The configuration file will have the following definitions:
    'schema' - file name including path that contains schema that the file is checked against.
               Example of schema file: doc/source/config/dqschemas/basicHDF.json
    'log_file' - defines log file. If not configured, the software will create default.log file in the working directory. 
    'verification_type' - defines how the file is verified. If the type is "hdf_tags", the file will be checked for the presence
    of listed tags; if the type is "hdf_structure", the tags, and listed attributes are checked.

    This test can be done at the end of data collection to verify that the collected data file is not
    corrupted.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cfname", help="configuration file name")
    parser.add_argument("fname", help="file name to do the quality checks on")

    args = parser.parse_args()

    conf = args.cfname
    fname = args.fname
    
    conf = arg[1]
    fname = arg[2]
    
    if hdf.verify(conf, fname):
        print ('All tags exist and meet conditions')
    else:
        print ('Some of the tags do not exist or do not meet conditions, check log file')

def pv_check(arg):
    """
    Please make sure the installation :ref:`pre-requisite-reference-label` are met.

    This example shows how to verify that the list of PV/PV-value conditions listed
    in the pvs.jason configured file are satisfied.
    This example takes one mandatory command line argument:
    conf: a string defining the configuration file. If only path is defined, the name 'dqconfig_test.ini'

    The configuration file will have the following definitions:
    'pv_file' - file name including path that contain process variables requirements. Example of pv file: 
                     doc/source/config/dqschemas/pvs.json
    'log_file' - defines log file. If not configured, the software will create default.log file in the working directory.

    This test can be done at the beginning of a scan to confirm mandatory process 
    variables are accessible and their values are within acceptable range.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cfname", help="configuration file name")

    args = parser.parse_args()
    conf = args.cfname

    if pv.verify(conf):
        print ('All PVs listed in pvs.json exist and meet conditions')
    else:
        print ('Some of the PVs listed in pvs.json do not exist or do not meet conditions')


def monitor_quality_check(arg):
    """
    Please make sure the installation :ref:`pre-requisite-reference-label` are met.

    This example shows how to verify newly created or modified files in a monitored folder.
    This example takes three mandatory command line arguments:
    conf: a string defining the configuration file. If only path is defined, the name 'dqconfig_test.ini'
    will be added as default
    folder: the folder to monitor
    num_files: an integer value specifying how many files will be processed

    The configuration file will have the following definitions:
    'limits' - file name including path that contains dictionary of limit values that will be applied to verify quality check calculations.
               Example of limits file: doc/source/config/dqschemas/limits.json
    'log_file' - defines log file. If not configured, the software will create default.log file in the working directory.
    'extensions' - list of file extensions that the script will monitor for.

    This test can be done at during data collection to confirm data quality
    values are within acceptable range.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cfname", help="configuration file name")
    parser.add_argument("fname", help="folder name to monitor for files")
    parser.add_argument("numfiles", help="number of files to monitor for")

    args = parser.parse_args()

    conf = args.cfname
    fname = args.fname
    num_files = args.numfiles

    bad_indexes = dmonitor.verify(conf, fname, int(num_files))
    return bad_indexes

def monitor_check(arg):
    """
    Please make sure the installation :ref:`pre-requisite-reference-label` are met.

    This example shows how to verify newly created or modified files in a monitored folder. This test
    will be used if the data of the same type (i.e. "data" or "data_dark" or "data_white) is collected
    in multiple files.

    This example takes four mandatory and one optional command line arguments:
    conf: a string defining the configuration file. If only path is defined, the name 'dqconfig_test.ini'
    will be added as default
    folder: the folder to monitor
    type: a string defining data type being processed; i.e. 'data_dark', 'data_white' or 'data'.
    num_files: an integer value specifying how many files will be processed
    report_by_files: a boolean value defining how the bad indexes should be reported. If True,
    the bad indexes will be sorted by files the image belongs to, and the indexes will be relative
    to the files. If False, the bad indexes are reported as a list of all indexes in sequence that
    did not pass quality checks.

    The configuration file will have the following definitions:
    'limits' - file name including path that contains dictionary of limit values that will be applied to verify quality check calculations.
               Example of limits file: doc/source/config/dqschemas/limits.json
    'log_file' - defines log file. If not configured, the software will create default.log file in the working directory.
    'extensions' - list of file extensions that the script will monitor for.

    This test can be done at during data collection to confirm data quality
    values are within acceptable range.

    """
    
    parser = argparse.ArgumentParser()
    parser.add_argument("cfname", help="configuration file name")
    parser.add_argument("fname", help="folder name to monitor for files")
    parser.add_argument("type", help="data type to be verified (i.e. data_dark, data_white, or data)")
    parser.add_argument("numfiles", help="number of files to monitor for")
    parser.add_argument("repbyfile", help="boolean value defining how the bad indexes should be reported.")

    args = parser.parse_args()

    conf = args.cfname
    fname = args.fname
    dtype = args.type
    num_files = args.numfiles
    report_by_file = args.repbyfile

    bad_indexes = monitor.verify(conf, fname, dtype, int(num_files), report_by_file)
    print json.dumps(bad_indexes)
    return bad_indexes


def dquality_check(arg):
    """
    Please make sure the installation :ref:`pre-requisite-reference-label` are met.

    This example shows how to verify the quality of data in an HDF file.
    This example takes two mandatory command line arguments:
    conf: a string defining the configuration file. If only path is defined, the name 'dqconfig_test.ini'
    file: a file to be verified.

    The configuration file will have the following definitions:
    'limits' - file name including path that contains dictionary of limit values that will be applied to verify quality check calculations.
               Example of limits file: doc/source/config/dqschemas/limits.json
    'log_file' - defines log file. If not configured, the software will create default.log file in the working directory.

    The detailed results are stored into configured report file.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cfname", help="configuration file name")
    parser.add_argument("fname", help="file name to do the quality checks on")    
    
    args = parser.parse_args()

    conf = args.cfname
    fname = args.fname

    bad_indexes = data.verify(conf, fname)
    print json.dumps(bad_indexes)
    return bad_indexes


def dependency_check(arg):
    """
    Please make sure the installation :ref:`pre-requisite-reference-label` are met.

    This example shows how to verify an HDF file dependencies.

    This example takes two mandatory command line arguments:
    conf: a string defining the configuration file. If only path is defined, the name 'dqconfig_test.ini'
    file: a file to be verified for dependencies according to schema.

    The configuration file will have the following definitions:
    'dependencies' - file name including path that contain dependecy schema. Example of dependency schema: 
                     doc/source/config/dqschemas/dependencies.json
    'log_file' - defines log file. If not configured, the software will create default.log file in the working directory.

    This test can be done at the end of data collection to verify that the collected data file is not
    corrupted.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cfname", help="configuration file name")
    parser.add_argument("fname", help="file name to do the quality checks on")

    args = parser.parse_args()

    conf = args.cfname
    fname = args.fname

    if dependency.verify(conf, file):
        print ('All dependecies are satisfied')
    else:
        print ('Some dependecies are not satisfied, see log file')


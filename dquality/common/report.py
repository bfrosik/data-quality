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
This file contains functions used to report results of quality checks and functions
facilitating logger.

"""

import pprint

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['report_results',
           'add_bad_indexes',
           'add_bad_indexes_per_file',
           'report_bad_indexes']


def report_results(aggregate, type, filename, report_file):
    """
    This function reports results of quality checks to a file or console
    if the file is not defined.

    Parameters
    ----------
    aggregate : Aggregate
        an instance holding result values for the data of one type

    type : str
        a string characterizung the data type (i.e. data_dark, data_white or data)

    filename : str
        name of the verified file

    report_file : file
        a file where the report will be written, or None, if written to a console

    Returns
    -------
    None
    """

    if report_file is None:
        if filename is not None:
            print (filename + '\n')
        print (type + '\n')
        pprint.pprint(aggregate, depth=3)
    else:
        if filename is not None:
            report_file.write(filename+ '\n')
        report_file.write(type+ '\n')
        pprint.pprint(aggregate, report_file)

def add_bad_indexes(aggregate, type, bad_indexes):
    """
    This function gets bad indexes from aggregate instance and creates an entry in
    bad_indexes dictionary. The bad_indexes dictionary will have added an entry for the given type.
    The entry is a list of all indexes of slices that did not pass quality checks.

    Parameters
    ----------
    aggregate : Aggregate
        an instance holding result values for the data of one type
    type : str
        a string characterizung the data type (i.e. data_dark, data_white or data)
    bad_indexes : dictionary
        a dictionary structure that the bad indexes will be written to
    Returns
    -------
    None
    """

    list = []
    for key in aggregate['bad_indexes'].keys():
        list.append(key)
    bad_indexes[type] = list


def add_bad_indexes_per_file(aggregate, type, bad_indexes, file_indexes):
    """
    This function gets bad indexes from aggregate instance and creates an entry in
    bad_indexes dictionary. The bad_indexes dictionary will have added an entry for the given type.
    The entry is a dictionary of files that were processed with lists of all indexes of slices
    in the file that did not pass quality checks.

    Parameters
    ----------
    aggregate : Aggregate
        an instance holding result values for the data of one type

    type : str
        a string characterizung the data type (i.e. data_dark, data_white or data)

    bad_indexes : dictionary
        a dictionary structure that the bad indexes will be written to

    file_indexes : dictionary
        a dictionary with filenames as keys, and starting indexes as values

    Returns
    -------
    None
    """

    def get_next_file_index(files_count, file_indexes):
        files_count -= 1
        if files_count > 0:
            next_file = it.next()
            next_file_index = file_indexes[next_file]
        else:
            next_file_index = -1
            next_file = None
        return next_file_index, next_file, files_count

    list = []
    files_count = len(file_indexes)
    dict = {}
    offset = 0
    it = iter(file_indexes.keys())
    current_file = it.next()
    current_file_index = file_indexes[current_file]
    next_file_index, next_file, files_count = get_next_file_index(files_count, file_indexes)
    for key in aggregate['bad_indexes'].keys():
        if key == current_file_index:
            dict[current_file] = list
            list = []
            offset = current_file_index
            current_file = next_file
            current_file_index = next_file_index
            next_file_index, next_file, files_count = get_next_file_index(files_count, file_indexes)
        list.append(key - offset)

    dict[current_file] = list
    bad_indexes[type] = dict


def report_bad_indexes(bad_indexes, report_file):
    """
    This function gets bad_indexes dictionary and reports them in a file, if one is defined
    or on the console otherwise.

    Parameters
    ----------
    bad_indexes : dictionary
        a dictionary structure that the bad indexes will be written to

    report_file : file
        a file where the report will be written, or None, if written to a console

    Returns
    -------
    None
    """

    if report_file is None:
        print ('bad indexes')
        pprint.pprint(bad_indexes, depth=3)
    else:
        report_file.write('bad indexes')
        pprint.pprint(bad_indexes, report_file)

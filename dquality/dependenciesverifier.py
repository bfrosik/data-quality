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
This application assumes there is a 'config.ini' file that contains parameters required to run the application:

'file' - hd5 file
'dependencies' - a file that includes dependencies between hd5 tags

"""

import sys
import json
import h5py
from configobj import ConfigObj

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['verify_pv']

config = ConfigObj('config.ini')


def read_pv(pv):
    return False

def lt(value, limit):
    """
    This function returns True if value parameter is less than limit parameter, False otherwise..

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
    This function returns True if value parameter is less than or equal to limit parameter, False otherwise..

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
    This function returns True if value parameter is equal to limit parameter, False otherwise..

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
    This function returns True if value parameter is greater than or equal to limit parameter, False otherwise..

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
    This function returns True if value parameter is greater than limit parameter, False otherwise..

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

def state(value, limit):
    """
    This function takes boolean "value" parameter and string "limit" parameter that can be either 'True' or 'False'.
    The limit is converted to string and compared with the value. The function returns True if the boolean values are
    equal, False otherwise.

    Parameters
    ----------
    value : numeric
        value

    limit : str
        limit value

    Returns
    -------
    boolean
    """
    if limit == 'True':
        return value == True
    else:
        return value == False

class TagValue:
    value = 0
    def __init__(self, tag):
        self.tag = tag
    def set_value(self,value):
        self.value = value
    def get_value(self):
        return self.value

def find_value(tag, dset):
    tag_def = tag.split()
    if len(tag_def) == 1:
        return dset.value
    else:
        if tag_def[1] == 'dim':
            axis = tag_def[2]
            return dset.shape[int(axis)]

function_mapper = {'less_than':lt, 'less_or_equal':le, 'equal':eq, 'greater_or_equal':ge, 'greater_than':gt, 'state':state}

def verify_list(file, list, relation):
    print ('next list')
    # create dictionary of tag : tag with parameters for fast lookup
    anchor_tag = TagValue(list[0])
    tags = {}
    for long_tag in list:
        tags[long_tag.split()[0]] = TagValue(long_tag)

    def func(name, dset):
        if len(list) != 0 and isinstance(dset, h5py.Dataset):
            tag = dset.name
            try:
                full_tag = tags[tag].tag
                list.remove(full_tag)
                value = find_value(full_tag, dset)
                tags[tag].set_value(value)
                if full_tag == anchor_tag.tag:
                    anchor_tag.set_value(value)
                    del tags[tag]

            except KeyError:
                pass

    file_h5 = h5py.File(file, 'r')
    file_h5.visititems(func)

    res = True
    for tag in tags:
        if not function_mapper[relation](tags.get(tag).get_value(), anchor_tag.get_value()):
            print ('the ' + tag + ' value is ' + str(tags.get(tag).get_value()) + ' but should be ' + relation + ' ' + str(anchor_tag.get_value()))
            res = False

    return res

def verify_dependencies():
    """
    This function reads the json 'dependencies' file from the config.ini.
    This file contains dictionary with keys of relations between tags.
    The value is a list of lists. The relation applies to the tags in inner list respectively. For example if the
    relation is "equal", all tags in each inner list must be equal,The outer list hold the lists that app;y the relation.
    A first element in a inner list is an "anchor" element, so all elements are compared to it. This is important for
    the "les_than" type of relation, when the order of parameters is important.

    The allowed keys are:
    "less_than" - the PV value must be less than attribute value
    "less_or_equal" - the PV value must be less than or equal attribute value
    "equal" - the PV value must be equal to attribute value
    "greater_or_equal" - the PV value must be greater than or equal attribute value
    "greater_than" - the PV value must be greater than attribute value

    The tag in a 'dependencies' file can be an hd5 tag, or can have appended keyword "dim" and an numeric value
    indicating axis. If the tag is simple hd5 tag, the verifier compares the value of this tag. If it has the
    "dim" keyword appended, the verifier compares a specified dimension.

    Any vakue that does not agree with the configured relation is reported (printed for now).
    The function returns True if no error was found and False otherwise.

    Parameters
    ----------
    None

    Returns
    -------
    boolean
    """
    res = True

    try:
        file = config['dependencies']
        with open(file) as data_file:
            dependencies = json.loads(data_file.read())

    except KeyError:
        print ('config error: dependencies not configured')
        sys.exit(-1)

    try:
        file = config['file']
    except KeyError:
        print ('config error: neither directory or file configured')
        sys.exit(-1)

    i = 0
    for relation in dependencies:
        batch = dependencies[relation]
        for tag_list in batch:
            res = verify_list(file, tag_list, relation)

    return res

if __name__ == '__main__':
    """
    This is the main function called when the application starts.
    It reads the configuration for the file defining mandatory process variables.
    It calls the verify_pv function that does the verification.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    verify_dependencies()



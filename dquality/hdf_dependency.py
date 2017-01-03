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
Please make sure the installation :ref:`pre-requisite-reference-label` are met.

This module verifies that each of the PVs listed in the configuration file
exist and their values are set within the predefined range.

The results will be reported in a file (printed on screen for now).
An error will be reported back to UI via PV.
"""

import os
import sys
import json
import h5py
import dquality.common.utilities as utils
from dquality.common.utilities import lt, le, eq, ge, gt


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'verify',
           'verify_list',
           'find_value']

function_mapper = {'less_than': lt, 'less_or_equal': le,
                   'equal': eq, 'greater_or_equal': ge, 'greater_than': gt}

def init(config):
    """
    This function initializes global variables. It gets values from the configuration file, evaluates and processes
    the values. If mandatory file or directory is missing, the script logs an error and exits.

    Parameters
    ----------
    config : str
        configuration file name, including path

    Returns
    -------
    logger : Logger
        logger instance

    dep : dictionary
        a dictionary containing dependency values read from the configured 'dependencies' file

    """
    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    dependencies = utils.get_file(conf, 'dependencies', logger)
    if dependencies is None:
        sys.exit(-1)

    with open(dependencies) as file:
        dep = json.loads(file.read())

    return logger, dep


class TagValue:
    value = 0

    def __init__(self, tag):
        self.tag = tag

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value


def find_value(tag, dset):
    """
    This function takes tag parameter and a corresponding dataset from
    the hd5 file. The tag can be a simple hd5 member tag or extended tag.
    This function assumes that the extended tag is a string containing
    hd5 tag, a word indicating the tag category (i.e. "*dim*" meaning
    dimension), and a parameter (i.e. numeric index). In the case of a
    simple hd5 tag the function returns a value of this member.
    In the second case the function returns decoded value, in the
    case of "dim" category, it returns the indexed dimension.

    Parameters
    ----------
    tag : str
        a simple hd5 tag or extended

    dset : dataset
        hd5 dataset corresonding to the tag parameter

    Returns
    -------
    value of decoded tag
    """

    tag_def = tag.split()
    if len(tag_def) == 1:
        return dset.value
    else:
        if tag_def[1] == 'dim':
            axis = tag_def[2]
            return dset.shape[int(axis)]

def verify_list(file, list, relation, logger):
    """
    This function takes an hd5 file, a list of tags (can be extended)
    and a relation between the list members. First the method creates
    a tags dictionary from the list of tags. The key is a simple hd5
    tag, and the value is a newly created TagValue instance that
    contains extended tag (or simple tag if simple tag was in the
    list), and a placeholder for the value. The first tag from the
    list is retained as an anchor.

    The function travers through all tags in the given file. If the
    tag name is found in the tags dictionary, the ```find_value```
    method is called to retrieve a defined valueu referenced by the
    tag. The value is then added to the TagValue instance for this tag.

    When all tags are processed the function iterates over the tags
    dictionary to find if the relation between anchor value and other
    values can be verified. If any relation is not true, a report is
    printed for this tag, and the function will return ```False```.
    Otherwise the function returns ```True```.

    Parameters
    ----------
    file : file
        an hd5 file to be verified

    list : list
        list of extended or simple hd5 tags

    relation : str
        a string specifying the relation between tags in the list

    logger : Logger
        a Logger instance

    Returns
    -------
    boolean
    """
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
        if not function_mapper[relation](
                tags.get(tag).get_value(),
                anchor_tag.get_value()):
            logger.warning('the ' + tag + ' value is ' +
                           str(tags.get(tag).get_value()) +
                           ' but should be ' + relation +
                           ' ' + str(anchor_tag.get_value()))
            res = False

    return res


def verify(conf, file):
    """
    This function reads the json "*dependencies*" file from the 
    :download:`dqconfig.ini <../../../config/default/dqconfig.ini>` file.
    This file contains dictionary with keys of relations between tags.
    The value is a list of lists. The relation applies to the tags in
    inner list respectively. For example if the relation is "*equal*",
    all tags in each inner list must be equal,The outer list hold the
    lists that apply the relation. A first element in a inner list is
    an "*anchor*" element, so all elements are compared to it. This
    is important for the "*less_than*" type of relation, when the
    order of parameters is important.

    The allowed keys are:

    - "*less_than*" - the PV value must be less than attribute value
    - "*less_or_equal*" - the PV value must be less than or equal attribute value
    - "*equal*" - the PV value must be equal to attribute value
    - "*greater_or_equal*" - the PV value must be greater than or equal attribute value
    - "*greater_than*" - the PV value must be greater than attribute value

    The tag in a "*dependencies*" file can be an hd5 tag, or can have
    appended keyword "*dim*" and an numeric value indicating axis. If
    the tag is simple hd5 tag, the verifier compares the value of this tag.
    If it has the "*dim*" keyword appended, the verifier compares a
    specified dimension.

    Any vakue that does not agree with the configured relation is
    reported (printed for now). The function returns True if no error
    was found and False otherwise.

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
    logger, dependencies = init(conf)
    if not os.path.isfile(file):
        logger.error(
            'parameter error: file ' +
            file + ' does not exist')
        sys.exit(-1)

    res = True
    i = 0

    for relation in dependencies:
        batch = dependencies[relation]
        for tag_list in batch:
            if not verify_list(file, tag_list, relation, logger):
                res = False

    if res:
        logger.info('All dependecies are satisfied')

    return res

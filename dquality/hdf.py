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

This file contains verification functions related to the file structure.
It reads configuration parameters "*schema_type*" and "*schema*" to
determine first which kind of file verification is requested, and a
schema that defines mandatory parameters. If any of the parameters is
not configured, it is assumed no file structure verification is requested.

"""
import sys
import h5py
import json
import os.path

import dquality.common.utilities as utils

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['init',
           'report_items',
           'verify',
           'tags',
           'structure']


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

    tags : dictionary
        a dictionary containing tag and attributes values read from the configured 'schema' file

    """
    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    schema = utils.get_file(conf, 'schema', logger)
    if schema is None:
        sys.exit(-1)

    with open(schema) as file:
        tags = json.loads(file.read())

    try:
        type = conf['verification_type']
    except KeyError:
        logger.error('config error: verification type not configured')
        sys.exit(-1)

    if type != 'hdf_structure' and type != 'hdf_tags':
        logger.error('configured verification type ' + type + ' is not supported')
        sys.exit(-1)

    return logger, tags, type


def report_items(list, text1, text2, logger):
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

    logger : Logger
        a Logger instance

    Returns
    -------
    None
    """
    if len(list) > 0:
        logger.warning(text1 + text2)
        for item in list:
            logger.warning('    - ' + item)


def structure(file, required_tags, logger):
    """
    This method is used when a file of hdf type is given.
    All tags and array dimensions are verified against a schema.
    (see :download:`schemas/tags.json <../../../config/default/schemas/tags.json>` 
    example file).

    Parameters
    ----------
    file : str
        File Name including path

    schema : str
        Schema file name

    logger : Logger
        a Logger instance

    Returns
    -------
    None

    """
    class Result():
        res = True

    def check_dim(dset, attr):
        required_dim = attr.get('dim')
        required_dim_copy = utils.copy_list(required_dim)
        dim = dset.shape
        if len(dim) == len(required_dim):
            for i in range(len(dim)):
                try:
                    required_dim_copy.remove(dim[i])
                except ValueError:
                    logger.warning('ValueError: The dataset ' + dset.name +
                          ' dimension ' + str(i) +
                          ' is wrong: it is [' +
                          str(dset.shape[i]) + '] but should be [' +
                          str(required_dim[i]) + ']')
                    res.res = False
        else:
            logger.warning('The dataset ' + dset.name + ' dimensions: ' +
                  str(dset.shape) + ' but should be ' + str(required_dim))
            res.res = False

    def func(name, dset):
        if isinstance(dset, h5py.Dataset):
            tag = dset.name
            tag_attribs = required_tags.get(tag)
            if tag_attribs is not None:
                tag_list.remove(tag)
                attrib_list = utils.key_list(tag_attribs)
                for key in tag_attribs:
                    if len(attrib_list) > 0:
                        if key == 'dim':
                            attrib_list.remove(key)
                            check_dim(dset, tag_attribs)
                        else:
                            attr = dset.attrs.get(key)
                            if attr is not None:
                                attr_str = attr.decode('utf-8')
                                if attr_str != tag_attribs.get(key):
                                    logger.warning('incorrect attribute in ' +
                                          tag + ': is ' +
                                          key + ':' +
                                          attr_str + ' but should be ' +
                                          key + ':' +
                                          tag_attribs.get(key))
                                    res.res = False
                                attrib_list.remove(key)
                report_items(
                    attrib_list,
                    'the following attributes are missing in tag ',
                    tag,
                    logger)

    res = Result()
    tag_list = utils.key_list(required_tags)
    file_h5 = h5py.File(file, 'r')
    file_h5.visititems(func)
    if res.res:
        return True
    else:
        report_items(tag_list, 'the following tags are missing: ', '', logger)
        return False


def tags(file, required_tags, logger):
    """
    This method is used when a file of hdf type is given.
    All tags from the hdf file are added in the filetags list.
    Then the schema is evaluated for tags. With each tag discovered
    it checks whether there is matching tag in the filetags list.
    If a tag is missing, the function exits with False.
    Otherwise, it will return True.

    Parameters
    ----------
    file : str
        File Name including path

    schema : str
        Schema file name

    logger : Logger
        a Logger instance

    Returns
    -------
    True if verified
    False if not verified

    """

    tag_list = utils.key_list(required_tags)

    class Result:

        def __init__(self):
            self.result = True

        def missing_tag(self):
            self.result = False

        def is_verified(self):
            return self.result

    result = Result()
    filetags = []

    def func(name, dset):
        if isinstance(dset, h5py.Dataset):
            filetags.append(dset.name)

    file_h5 = h5py.File(file, 'r')
    file_h5.visititems(func)

    for tag in tag_list:
        if tag not in filetags:
            logger.warning('tag ' + tag + ' not found')
            result.missing_tag()

    return result.is_verified()


def verify(conf, file):
    """
    This is the main function called when the structureverifier
    application starts. It reads the configuration file for
    "*verification_type*" to verify "*hdf_structure*" or "*hdf_tags*".

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

    logger, required_tags, type = init(conf)
    if not os.path.isfile(file):
        logger.error(
            'parameter error: file ' +
            file + ' does not exist')
        sys.exit(-1)

    if type == 'hdf_structure':
        ret = structure(file, required_tags, logger)
        if ret:
            logger.info('All required tags exist and meet conditions')
            return ret
    elif type == 'hdf_tags':
        ret = tags(file, required_tags, logger)
        if ret:
            logger.info('All required tags exist')
            return ret



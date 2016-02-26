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
This file contains verification functions related to the file structure.
It reads configuration parameters "schema_type" and 'schema' to determine first which kind of file verification is requested, and a schema that defines mandatory parameters.
If any of the parameters is not configured, it is assumed no file structure verification is requested.

"""

import os.path
import h5py
import json
from configobj import ConfigObj
from common.utilities import copy_list, key_list, report_items

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['verify_real_time_hd5',
           'verify_structure']

config = ConfigObj('config.ini')

def report_structure_hd5(file, schema):
    def check_dim(dset, attr):
        required_dim = attr.get('dim')
        required_dim_copy = copy_list(required_dim)
        dim = dset.shape
        if len(dim) == len(required_dim):
            for i in range(len(dim)):
                try:
                    required_dim_copy.remove(dim[i])
                except ValueError:
                    print ('the dataset '  + dset.name + '  dimentions are: ' + str(dset.shape) + ' but should be ' + str(required_dim))
        else:
            print ('the dataset '  + dset.name + '  dimentions are: ' + str(dset.shape) + ' but should be ' + str(required_dim))

    def func(name, dset):
        if isinstance(dset, h5py.Dataset):
            tag = dset.name
            tag_attribs = required_tags.get(tag)
            if tag_attribs is not None:
                tag_list.remove(tag)
                attrib_list = key_list(tag_attribs)
                for key in tag_attribs:
                    if len(attrib_list) > 0:
                        if key == 'dim':
                            attrib_list.remove(key)
                            check_dim(dset, tag_attribs)
                        else:
                            attr = dset.attrs.get(key)
                            if attr is not None:
                                if attr != tag_attribs.get(key):
                                    print ('incorrect attribute in ' + tag + ': is ' + key + ':' + attr + ' but should be ' + key + ':' + tag_attribs.get(key))
                                attrib_list.remove(key)
                report_items(attrib_list, 'the following attributes are missing in tag ', tag)

    required_tags = {}
    with open('schemas/basicHD5.json') as data_file:
        required_tags = json.loads(data_file.read()).get('required_tags')

    tag_list = key_list(required_tags)
    file = '/local/bfrosik/DQ/test/data/test_01.h5'
    file_h5 = h5py.File(file, 'r')
    file_h5.visititems(func)
    report_items(tag_list, 'the following tags are missing: ', '')

def verify_real_time_hd5(file, schema):
    """
    This method is used when a file of hd5 type is given. 
    All tags from the hd5 file are added in the filetags list.
    Then the schema is evaluated for tags. With each tag discovered it checks whether there is matching tag in the filetags list.
    If a tag is missing, the function exits with False.
    Otherwise, it will return True.
     
    Parameters
    ----------
    file : str
        File Name including path
    
    schema : str
        Schema file name

    Returns
    -------
    True if verified
    False if not verified
        
    """

    with open('schemas/basicHD5.json') as data_file:
        required_tags = json.loads(data_file.read()).get('required_tags')

    tag_list = key_list(required_tags)

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
        if result.is_verified():
            if tag not in filetags:
                print ('tag ' + tag + ' not found')
                result.missing_tag()

    return result.is_verified()

def verify_structure(file):
    """
    This method reads configuration parameter 'schema-type'. If not configured, the function returns True, 
    as no verification is needed.
    In case the type is set, the follow up logic determines, what type of verification should be applied.
    Currently, the HD5 type is supported.
    The function then reads the schema file from config. If not configured, the function returns True, as 
    no verification is needed.
    Otherwise, it will call the appropriate verification function and will return the result.
     
    Parameters
    ----------
    file : str
        File Name including path
    
    Returns
    -------
    True if verified
    False if not verified
        
    """
    try:
        type = config['verification_type']
        if type == 'report_hd5':
            try:
                schema = config['schema']
                if not os.path.isfile(schema):
                    print ('configuration error: schema file ' + schema + ' does not exist')
                    return False
                return report_structure_hd5(file, schema)
            except KeyError:
                return True
        if type == 'real_time_hd5':
            try:
                schema = config['schema']
                if not os.path.isfile(schema):
                    print ('configuration error: schema file ' + schema + ' does not exist')
                    return False
                return verify_real_time_hd5(file, schema)
            except KeyError:
                return True

    except KeyError:
        return True
